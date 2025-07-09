from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.v1.db.database import get_mongo_client, close_mongo_connection
from app.v1.db.mongo_logger import setup_mongo_logging
import logging

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager to handle database startup and shutdown
    """
    # Startup: Initialize MongoDB connection
    await get_mongo_client()

    # Setup MongoDB logging
    await setup_mongo_logging()

    logger.info("MongoDB connection and logging initialized")

    yield

    # Shutdown: Close MongoDB connection
    await close_mongo_connection()

    logger.info("MongoDB connection closed")
