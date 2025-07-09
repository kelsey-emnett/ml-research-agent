import asyncio
import logging
from app.v1.repositories.errors import ErrorRepository
from app.v1.utils.exception_handling import handle_exception

logger = logging.getLogger(__name__)


class MongoDBHandler(logging.Handler):
    """
    Custom logging handler that writes log records to MongoDB
    """

    def __init__(self, level=logging.WARNING):
        super().__init__(level)
        self.loop = None
        self.error_repository = ErrorRepository()

    def emit(self, record):
        """
        Write the log record to MongoDB
        Only logs WARNING and ERROR levels
        """
        if record.levelno >= logging.WARNING:  # Only log warnings and errors
            try:
                if self.loop is None:
                    try:
                        self.loop = asyncio.get_running_loop()
                    except RuntimeError:
                        self.loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(self.loop)

                asyncio.run_coroutine_threadsafe(
                    self.error_repository.log_error(record), self.loop
                )
            except Exception as e:
                # Use a fallback logger in case of MongoDB connection issues
                fallback = logging.getLogger("fallback")
                fallback.error(f"Failed to log to MongoDB: {e}")


@handle_exception(
    logger, operation_desc="setting up MongoDB logging", include_error_type=True
)
async def setup_mongo_logging():
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
