from pymongo import MongoClient
from azure.storage.blob import BlobServiceClient, ContainerClient

# MongoDB connection
def get_mongo_client(uri):
    try:
        client = MongoClient(uri)
        db = client['cosmosdb-mongodb-v1']
        users_collection = db['Users']
        return users_collection
    except Exception as e:
        print(f"Error connecting to MongoDB: {str(e)}")
        return None

# Blob Storage connection
def get_blob_container_client(connection_string, container_name):
    try:
        blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        container_client = blob_service_client.get_container_client(container_name)
        return container_client
    except Exception as e:
        print(f"Error connecting to Blob Storage: {str(e)}")
        return None