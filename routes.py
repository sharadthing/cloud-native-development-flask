from flask import Blueprint, request, jsonify, send_file
from io import BytesIO
from azure.storage.blob import BlobServiceClient
from datetime import datetime

# Initialize Blueprint
bp = Blueprint('routes', __name__)

# Blob Storage configuration
BLOB_CONNECTION_STRING = 'DefaultEndpointsProtocol=https;AccountName=com682storagev1;AccountKey=kz99G6p98N/bdlTZ9F4Q/tWqNONgrl47+U9W3Z0i2eo1pv4kPakDkOiuDYRIGLVW/iUfeHlk6gzb+AStMOxwbA==;EndpointSuffix=core.windows.net'
BLOB_CONTAINER_NAME = 'com682databsecontaineerblob'

# Get Blob container client
blob_service_client = BlobServiceClient.from_connection_string(BLOB_CONNECTION_STRING)
container_client = blob_service_client.get_container_client(BLOB_CONTAINER_NAME)

@bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({"msg": "Missing email or password"}), 400

    # Dummy user validation for demonstration purposes
    if email == "user@example.com" and password == "password":
        return jsonify({"msg": "Login successful"}), 200
    else:
        return jsonify({"msg": "Bad email or password"}), 401

@bp.route('/upload-file', methods=['POST'])
def upload_file():
    file = request.files['file']
    file_name = request.form.get('file_name')
    if not file or not file_name:
        return jsonify({"msg": "No file or file name provided"}), 400

    file_extension = file.filename.rsplit('.', 1)[1].lower()
    subfolder = 'others'
    if file_extension in {'jpg', 'jpeg', 'png', 'gif'}:
        subfolder = 'images'
    elif file_extension in {'mp4', 'avi', 'mov'}:
        subfolder = 'videos'
    elif file_extension in {'mp3', 'wav', 'aac'}:
        subfolder = 'audios'
    elif file_extension in {'pdf', 'txt', 'doc', 'docx'}:
        subfolder = 'documents'

    filename = f"{subfolder}/{file_name}.{file_extension}"
    file_url = f"https://com682storagev1.blob.core.windows.net/com682databsecontaineerblob/{filename}"
    date_created = datetime.utcnow().isoformat()

    try:
        blob_client = container_client.get_blob_client(filename)
        blob_client.upload_blob(file)
        blob_client.set_blob_metadata({
            'file_name': file_name,
            'url': file_url,
            'date_created': date_created
        })
        return jsonify({"msg": "File uploaded successfully"}), 200
    except Exception as e:
        return jsonify({"msg": f"Failed to upload file: {str(e)}"}), 500

@bp.route('/list-files', methods=['GET'])
def list_files():
    try:
        blob_list = container_client.list_blobs()
        files = []
        for blob in blob_list:
            blob_client = container_client.get_blob_client(blob.name)
            metadata = blob_client.get_blob_properties().metadata
            files.append({
                'file_name': metadata.get('file_name', blob.name),
                'url': metadata.get('url', ''),
                'date_created': metadata.get('date_created', '')
            })
        return jsonify(files), 200
    except Exception as e:
        return jsonify({"msg": f"Failed to list files: {str(e)}"}), 500

@bp.route('/get-file/<path:filename>', methods=['GET'])
def get_file(filename):
    try:
        blob_client = container_client.get_blob_client(filename)
        download_stream = blob_client.download_blob()
        file_extension = filename.rsplit('.', 1)[1].lower()
        content_type = 'application/octet-stream'
        if file_extension in {'jpg', 'jpeg', 'png', 'gif'}:
            content_type = 'image/' + file_extension
        elif file_extension == 'pdf':
            content_type = 'application/pdf'
        elif file_extension in {'mp4', 'avi', 'mov'}:
            content_type = 'video/' + file_extension
        elif file_extension in {'mp3', 'wav', 'aac'}:
            content_type = 'audio/' + file_extension
        elif file_extension in {'txt', 'doc', 'docx'}:
            content_type = 'text/plain'
        return send_file(BytesIO(download_stream.readall()), mimetype=content_type)
    except Exception as e:
        return jsonify({"msg": f"Failed to get file: {str(e)}"}), 500

@bp.route('/update-file/<path:filename>', methods=['PUT'])
def update_file(filename):
    file = request.files['file']
    if not file:
        return jsonify({"msg": "No file part"}), 400

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
