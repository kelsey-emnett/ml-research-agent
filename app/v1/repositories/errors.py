from app.v1.repositories.base import BaseRepository
from app.v1.schemas.errors import ErrorInput
import logging
from typing import Optional
from app.v1.utils.exception_handling import handle_exception

from app.v1.db.database import ERROR_COLLECTION

logger = logging.getLogger(__name__)


class ErrorRepository(BaseRepository):
    """
    Repository for error logging operations
    """

    def __init__(self):
        """
        Initialize repository with error collection name
        """

        super().__init__(ERROR_COLLECTION)
        """
        Log an error to the database

        Args:
            error_data (Dict): Error data to log

        Returns:
            str: ID of the inserted error document
        """

    @handle_exception(
        logger, operation_desc="logging error message.", include_error_type=True
    )
    async def log_error(
        self, record: logging.LogRecord, formatter: Optional[logging.Formatter] = None
    ):
        """
        Log an error to the database

        Args:
            record (logging.LogRecord): Log record to store
            formatter (Optional[logging.Formatter]): Optional formatter for the log message

        Returns:
            str: ID of the inserted error document
        """
        message = formatter.format(record) if formatter else record.getMessage()

        error_input = ErrorInput(
            level=record.levelname,
            message=message,
            module=record.module,
            funcName=record.funcName,
            lineno=record.lineno,
            pathname=record.pathname,
        )
        return await self.insert_one(error_input.model_dump())

    @handle_exception(
        logger,
        input_identifier_key="doi",
        operation_desc="getting recent error messages.",
        include_error_type=True,
    )
    async def get_recent_errors(self, limit=5):
        """
        Get the most recent errors from the database

        Args:
            limit (int): Maximum number of errors to return

        Returns:
            List[Dict]: List of recent error documents
        """
        return await self.find_many({}, limit=limit, sort=[("timestamp", -1)])
