from fastapi import FastAPI
from app.v1.db.database import get_mongo_client, close_mongo_connection
from app.v1.db.mongo_logger import setup_mongo_logging
import logging

logger = logging.getLogger(__name__)


def init_db(app: FastAPI):
    """
    Initialize database connection and setup MongoDB logging
    """

    @app.on_event("startup")
    async def startup_db_client():
        # Initialize MongoDB connection
        get_mongo_client()

        # Setup MongoDB logging
        setup_mongo_logging()

        logger.info("MongoDB connection and logging initialized")

    @app.on_event("shutdown")
    async def shutdown_db_client():
        # Close MongoDB connection
        close_mongo_connection()

        logger.info("MongoDB connection closed")
