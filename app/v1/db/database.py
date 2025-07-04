from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
import logging
import os
from dotenv import load_dotenv

# Configure basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# MongoDB connection details from environment variables
MONGO_URI = os.getenv("MONGODB_CONNECTION_STRING", "mongodb://localhost:27017/")
DB_NAME = os.getenv("MONGODB_DB_NAME", "ml-research-agent")
ERROR_COLLECTION = os.getenv("MONGODB_LOG_COLLECTION", "error-collection")

# Global client object to maintain connection
mongo_client = None
db = None


def get_mongo_client():
    """
    Returns a MongoDB client instance, creating it if needed
    """
    global mongo_client
    if mongo_client is None:
        try:
            mongo_client = MongoClient(
                MONGO_URI,
                tlsAllowInvalidCertificates=True,  # This replaces ssl_cert_reqs=CERT_NONE
                connectTimeoutMS=30000,
                serverSelectionTimeoutMS=30000,
            )

            # Verify connection is working
            mongo_client.admin.command("ping")
            logger.info("Successfully connected to MongoDB")
        except ConnectionFailure as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
    return mongo_client


def get_database():
    """
    Returns a reference to the database
    """
    global db
    if db is None:
        client = get_mongo_client()
        db = client[DB_NAME]
    return db


def get_error_collection():
    """
    Returns a reference to the error collection
    """
    database = get_database()
    return database[ERROR_COLLECTION]


def close_mongo_connection():
    """
    Closes the MongoDB connection
    """
    global mongo_client, db
    if mongo_client is not None:
        mongo_client.close()
        mongo_client = None
        db = None
        logger.info("MongoDB connection closed")
