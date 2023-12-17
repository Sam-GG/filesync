from flask import Flask, send_from_directory, request, jsonify
import os
import shutil
from datetime import datetime

app = Flask(__name__)

directory_path = os.path.dirname(__file__)  # Directory of the current script

@app.route('/files/<path:filename>')
def download_file(filename):
    return send_from_directory(directory_path, filename)

@app.route('/upload/<filename>', methods=['POST'])
def upload_file(filename):
    file_path = os.path.join(directory_path, filename)
    
    # Check if the file exists and create a backup
    if os.path.exists(file_path):
        backup_filename = "{}.bak_{}".format(filename, datetime.now().strftime("%Y%m%d%H%M%S"))
        backup_path = os.path.join(directory_path, backup_filename)
        shutil.copyfile(file_path, backup_path)
        print(f"Backup of the existing file created: {backup_path}")

    # Save the new file
    file = request.files['file']
    file.save(file_path)
    return jsonify({"message": "File uploaded successfully"}), 200

if __name__ == '__main__':
    app.run(debug=True)
