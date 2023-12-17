import os
import time
import http.client
import requests
from datetime import datetime, timezone
from urllib.parse import urlparse, urljoin
import urllib.request

# Pull in configuration
config = {}
with open('config.txt', 'r') as file:
    for line in file:
        key, value = line.strip().split(':', 1)
        key = key.strip()
        value = value.strip()
        config[key] = value

def get_utc_timestamp(file_path):
    """ Get the UTC timestamp of the file's last modification """
    timestamp = os.path.getmtime(file_path)
    return datetime.utcfromtimestamp(timestamp).replace(tzinfo=timezone.utc).timestamp()

def construct_headers():
    """ Construct headers for HTTP requests """
    return {
        "ngrok-skip-browser-warning": "true",
        "User-Agent": "Mozilla/5.0 (compatible; YourScript/1.0)"
    }

def handle_redirects(url, headers, redirect_limit=5):
    """ Handle HTTP redirects """
    if redirect_limit == 0:
        raise Exception("Reached redirect limit")

    conn = http.client.HTTPSConnection(urlparse(url).netloc)
    conn.request("HEAD", urlparse(url).path, headers=headers)
    response = conn.getresponse()

    if response.status in [301, 302, 303, 307, 308]:
        new_url = response.getheader('Location')
        return handle_redirects(urljoin(url, new_url), headers, redirect_limit - 1)
    
    return response

def get_server_file_modified_time(url):
    """ Get the last modified time of the server file """
    headers = construct_headers()
    try:
        response = handle_redirects(url, headers)
        if response.status == 200 and 'Last-Modified' in response.headers:
            server_time = datetime.strptime(response.headers['Last-Modified'], '%a, %d %b %Y %H:%M:%S GMT')
            return server_time.replace(tzinfo=timezone.utc).timestamp()
        else:
            return None
    except Exception as e:
        print(f"Error getting server file modified time: {e}")
        return None

def download_file(url, local_file_path):
    """ Download the file from the server """
    try:
        req = urllib.request.Request(url, headers=construct_headers())
        with urllib.request.urlopen(req) as response, open(local_file_path, 'wb') as file:
            file.write(response.read())
        print(f"Updated the file: {local_file_path}")
    except Exception as e:
        print(f"Failed to download the file: {e}")

def upload_file(url, local_file_path):
    """ Upload the file to the server """
    try:
        files = {'file': open(local_file_path, 'rb')}
        response = requests.post(url, files=files)
        if response.status_code == 200:
            print("File uploaded successfully.")
        else:
            print("Failed to upload the file.")
    except Exception as e:
        print(f"Error during file upload: {e}")

def check_and_update_file(local_file_path, server_url):
    """ Check if the local file is up-to-date with the server version and upload if newer """
    if not os.path.exists(local_file_path):
        print("Local file does not exist, downloading a new copy...")
        download_file(server_url, local_file_path)
        return

    local_file_modified_time = get_utc_timestamp(local_file_path)
    server_file_modified_time = get_server_file_modified_time(server_url)

    # Compare the timestamps
    if server_file_modified_time is not None:
        time_difference = local_file_modified_time - server_file_modified_time
        if abs(time_difference) <= int(config['rate'])+10:
            print("Local file is up-to-date.")
        elif server_file_modified_time > local_file_modified_time:
            print("Server file is newer, updating...")
            download_file(server_url, local_file_path)
        elif local_file_modified_time > server_file_modified_time:
            print("Local file is newer, uploading...")
            upload_file(server_url.replace('files/', 'upload/'), local_file_path)
    else:
        print("Could not determine the server file's last modified time.")


# Drivin
while True:
    check_and_update_file(config['path']+config['filename'], config['server']+config['filename'])
    time.sleep(int(config['rate']))  
