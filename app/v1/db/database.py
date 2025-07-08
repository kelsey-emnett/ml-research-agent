from motor.motor_asyncio import AsyncIOMotorClient
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
MONGO_URI = os.getenv("MONGODB_CONNECTION_STRING")
DB_NAME = os.getenv("MONGODB_DB_NAME")
ERROR_COLLECTION = os.getenv("MONGODB_ERROR_COLLECTION")
ARTICLE_COLLECTION = os.getenv("MONGODB_ARTICLE_COLLECTION")
CHAT_COLLECTION = os.getenv("MONGODB_CHAT_COLLECTION")

# Global client object to maintain connection
mongo_client = None
db = None


async def get_mongo_client():
    """
    Returns a MongoDB client instance, creating it if needed
    """
    global mongo_client
    if mongo_client is None:
        try:
            mongo_client = AsyncIOMotorClient(
                MONGO_URI,
                tlsAllowInvalidCertificates=True,  # This replaces ssl_cert_reqs=CERT_NONE
                connectTimeoutMS=30000,
                serverSelectionTimeoutMS=30000,
            )

            # Verify connection is working
            await mongo_client.admin.command("ping")
            logger.info("Successfully connected to MongoDB")
        except ConnectionFailure as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
    return mongo_client


async def get_database():
    """
    Returns a reference to the database
    """
    global db
    if db is None:
        client = await get_mongo_client()
        db = client[DB_NAME]
    return db


async def get_collection(collection: str):
    """
    Returns a reference to the error collection
    """
    database = await get_database()
    if collection == "error":
        return database[ERROR_COLLECTION]
    elif collection == "article":
        return database[ARTICLE_COLLECTION]
    elif collection == "chat":
        return database[CHAT_COLLECTION]
    else:
        raise ValueError("Invalid collection name")


async def get_article_collection():
    """
    Returns a reference to the error collection
    """
    database = await get_database()
    return database[ARTICLE_COLLECTION]


async def close_mongo_connection():
    """
    Closes the MongoDB connection
    """
    global mongo_client, db
    if mongo_client is not None:
        mongo_client.close()
        mongo_client = None
        db = None
        logger.info("MongoDB connection closed")
