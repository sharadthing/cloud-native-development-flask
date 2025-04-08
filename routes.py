from flask import Blueprint, request, jsonify
from db import get_mongo_client, get_blob_container_client
from io import BytesIO
import mimetypes
from bson import ObjectId
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash

# Initialize Blueprint
bp = Blueprint('routes', __name__)

# MongoDB and Blob Storage configuration
MONGO_URI = 'mongodb://hello-students:jBfJVncH9XuuIJVQEVO1WR7B6D5zLQYrgOU4xbGOWcESF8dMyzeTNuWBhMspzCmWY6nAg5MhW46dACDbndnPsg%3D%3D@hello-students.mongo.cosmos.azure.com:10255/cosmosdb-mongodb-v1?ssl=true&replicaSet=globaldb&retrywrites=false&maxIdleTimeMS=120000&appName=@hello-students@'
BLOB_CONNECTION_STRING = 'DefaultEndpointsProtocol=https;AccountName=com682storagev1;AccountKey=kz99G6p98N/bdlTZ9F4Q/tWqNONgrl47+U9W3Z0i2eo1pv4kPakDkOiuDYRIGLVW/iUfeHlk6gzb+AStMOxwbA==;EndpointSuffix=core.windows.net'
BLOB_CONTAINER_NAME = 'com682databsecontaineerblob'

# Get MongoDB collections
db = get_mongo_client(MONGO_URI)
admin_collection = db['Admin']
worker_collection = db['Workers']
container_client = get_blob_container_client(BLOB_CONNECTION_STRING, BLOB_CONTAINER_NAME)

# Admin Authentication
@bp.route('/admin/register', methods=['POST'])
def register_admin():
    data = request.json
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"message": "Email and password required"}), 400

    if admin_collection.find_one({"email": email}):
        return jsonify({"message": "Admin already exists"}), 400

    hashed_password = generate_password_hash(password)
    admin_collection.insert_one({"email": email, "password": hashed_password})

    return jsonify({"message": "Admin registered successfully"}), 201

@bp.route('/admin/login', methods=['POST'])
def login_admin():
    data = request.json
    email = data.get("email")
    password = data.get("password")

    admin = admin_collection.find_one({"email": email})
    if not admin or not check_password_hash(admin["password"], password):
        return jsonify({"message": "Invalid credentials"}), 401

    return jsonify({"message": "Login successful"}), 200

# Worker CRUD Endpoints
@bp.route('/workers', methods=['GET'])
def get_workers():
    status = request.args.get('status')
    search = request.args.get('search')
    
    query = {}
    
    if status and status in ['on', 'off', 'suspended']:
        query['site_access.working_status'] = status
    
    if search:
        query['$or'] = [
            {'personal_info.full_name': {'$regex': search, '$options': 'i'}},
            {'site_access.worker_id': {'$regex': search, '$options': 'i'}},
            {'contact_info.email': {'$regex': search, '$options': 'i'}}
        ]
    
    workers = list(worker_collection.find(query))
    
    for worker in workers:
        worker['_id'] = str(worker['_id'])
    
    return jsonify(workers), 200

@bp.route('/workers', methods=['POST'])
def create_worker():
    data = request.json
    
    if not all(key in data for key in ['personal_info', 'contact_info', 'emergency_contact', 'site_access']):
        return jsonify({'message': 'Missing required fields'}), 400
    
    data['site_access']['created_at'] = datetime.utcnow()
    
    result = worker_collection.insert_one(data)
    
    return jsonify({
        'message': 'Worker created successfully',
        'worker_id': str(result.inserted_id)
    }), 201

@bp.route('/workers/<worker_id>', methods=['GET'])
def get_worker(worker_id):
    try:
        worker = worker_collection.find_one({'_id': ObjectId(worker_id)})
        if not worker:
            return jsonify({'message': 'Worker not found'}), 404
        
        worker['_id'] = str(worker['_id'])
        return jsonify(worker), 200
    except:
        return jsonify({'message': 'Invalid worker ID'}), 400

@bp.route('/workers/<worker_id>', methods=['PUT'])
def update_worker(worker_id):
    data = request.json
    
    try:
        data.pop('_id', None)
        
        result = worker_collection.update_one(
            {'_id': ObjectId(worker_id)},
            {'$set': data}
        )
        
        if result.modified_count == 0:
            return jsonify({'message': 'Worker not found or no changes made'}), 404
        
        return jsonify({'message': 'Worker updated successfully'}), 200
    except:
        return jsonify({'message': 'Invalid worker ID'}), 400

@bp.route('/workers/<worker_id>', methods=['DELETE'])
def delete_worker(worker_id):
    try:
        result = worker_collection.delete_one({'_id': ObjectId(worker_id)})
        
        if result.deleted_count == 0:
            return jsonify({'message': 'Worker not found'}), 404
        
        return jsonify({'message': 'Worker deleted successfully'}), 200
    except:
        return jsonify({'message': 'Invalid worker ID'}), 400
