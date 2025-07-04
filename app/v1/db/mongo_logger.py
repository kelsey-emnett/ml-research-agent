import logging
import datetime
from app.v1.db.database import get_error_collection


class MongoDBHandler(logging.Handler):
    """
    Custom logging handler that writes log records to MongoDB
    """

    def __init__(self, level=logging.WARNING):
        super().__init__(level)

    def emit(self, record):
        """
        Write the log record to MongoDB
        Only logs WARNING and ERROR levels
        """
        if record.levelno >= logging.WARNING:  # Only log warnings and errors
            try:
                # Get the error collection
                error_collection = get_error_collection()

                # Create a document with only the essential fields
                log_entry = {
                    "timestamp": datetime.datetime.utcnow(),
                    "level": record.levelname,
                    "message": self.format(record),
                    "module": record.module,
                    "funcName": record.funcName,
                    "lineno": record.lineno,
                    "pathname": record.pathname,
                }

                # Insert the document
                error_collection.insert_one(log_entry)
            except Exception as e:
                # Use a fallback logger in case of MongoDB connection issues
                fallback = logging.getLogger("fallback")
                fallback.error(f"Failed to log to MongoDB: {e}")


def setup_mongo_logging():
    """
    Set up MongoDB logging for the application
    """
    # Get the root logger
    root_logger = logging.getLogger()

    # Create MongoDB handler
    mongo_handler = MongoDBHandler(level=logging.WARNING)

    # Add a formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    mongo_handler.setFormatter(formatter)

    # Add the handler to the root logger
    root_logger.addHandler(mongo_handler)

    # Set the logger level to ensure it captures warnings and errors
    root_logger.setLevel(logging.WARNING)

    return root_logger
