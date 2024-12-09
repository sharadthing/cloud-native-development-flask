from flask import Blueprint, request, jsonify, send_file
from db import get_mongo_client, get_blob_container_client
from io import BytesIO
import mimetypes
from datetime import datetime, timedelta

# Initialize Blueprint
bp = Blueprint('routes', __name__)

# MongoDB and Blob Storage configuration
MONGO_URI = 'mongodb://hello-students:jBfJVncH9XuuIJVQEVO1WR7B6D5zLQYrgOU4xbGOWcESF8dMyzeTNuWBhMspzCmWY6nAg5MhW46dACDbndnPsg%3D%3D@hello-students.mongo.cosmos.azure.com:10255/cosmosdb-mongodb-v1?ssl=true&replicaSet=globaldb&retrywrites=false&maxIdleTimeMS=120000&appName=@hello-students@'
BLOB_CONNECTION_STRING = 'DefaultEndpointsProtocol=https;AccountName=com682storagev1;AccountKey=kz99G6p98N/bdlTZ9F4Q/tWqNONgrl47+U9W3Z0i2eo1pv4kPakDkOiuDYRIGLVW/iUfeHlk6gzb+AStMOxwbA==;EndpointSuffix=core.windows.net'
BLOB_CONTAINER_NAME = 'com682databsecontaineerblob'

# Get MongoDB collection and Blob container client
users_collection = get_mongo_client(MONGO_URI)
container_client = get_blob_container_client(BLOB_CONNECTION_STRING, BLOB_CONTAINER_NAME)

@bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({"msg": "Missing email or password"}), 400

    print(f"Checking login for email: {email} and password: {password}")
    user = users_collection.find_one({"email": email})
    print(f"User found: {user}")

    if user and user['password'] == password:
        return jsonify({"msg": "Login successful"}), 200
    else:
        return jsonify({"msg": "Bad email or password"}), 401

@bp.route('/upload-file', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"msg": "No file part"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"msg": "No selected file"}), 400

    # Determine the subfolder based on file extension
    file_extension = file.filename.rsplit('.', 1)[1].lower()
    if file_extension in {'jpg', 'jpeg', 'png', 'gif'}:
        subfolder = 'images'
    elif file_extension in {'mp4', 'avi', 'mov'}:
        subfolder = 'videos'
    elif file_extension in {'mp3', 'wav', 'aac'}:
        subfolder = 'audios'
    elif file_extension in {'pdf', 'txt', 'doc', 'docx'}:
        subfolder = 'documents'
    else:
        subfolder = 'others'

    # Specify the path including subdirectory
    filename = f"{subfolder}/{file.filename}"

    try:
        blob_client = container_client.get_blob_client(filename)
        blob_client.upload_blob(file)
        return jsonify({"msg": "File uploaded successfully"}), 200
    except Exception as e:
        return jsonify({"msg": f"Failed to upload file: {str(e)}"}), 500

@bp.route('/list-files', methods=['GET'])
def list_files():
    try:
        blob_list = container_client.list_blobs()
        files = [blob.name for blob in blob_list]
        return jsonify(files), 200
    except Exception as e:
        return jsonify({"msg": f"Failed to list files: {str(e)}"}), 500

@bp.route('/get-file/<path:filename>', methods=['GET'])
def get_file(filename):
    try:
        blob_client = container_client.get_blob_client(filename)
        download_stream = blob_client.download_blob()

        # Guess the content type of the file
        content_type, _ = mimetypes.guess_type(filename)
        content_type = content_type or 'application/octet-stream'  # Fallback if unknown

        return send_file(BytesIO(download_stream.readall()), mimetype=content_type, as_attachment=True, attachment_filename=filename)
    except Exception as e:
        return jsonify({"msg": f"Failed to get file: {str(e)}"}), 500

@bp.route('/update-file/<path:filename>', methods=['PUT'])
def update_file(filename):
    if 'file' not in request.files:
        return jsonify({"msg": "No file part"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"msg": "No selected file"}), 400

    try:
        blob_client = container_client.get_blob_client(filename)
        blob_client.upload_blob(file, overwrite=True)
        return jsonify({"msg": "File updated successfully"}), 200
    except Exception as e:
        return jsonify({"msg": f"Failed to update file: {str(e)}"}), 500

@bp.route('/delete-file/<path:filename>', methods=['DELETE'])
def delete_file(filename):
    try:
        blob_client = container_client.get_blob_client(filename)
        blob_client.delete_blob()
        return jsonify({"msg": "File deleted successfully"}), 200
    except Exception as e:
        return jsonify({"msg": f"Failed to delete file: {str(e)}"}), 500
