import logging
import functools
import asyncio
from typing import TypeVar, Optional

logger = logging.getLogger(__name__)

# Define type variables for better type hints
T = TypeVar("T")
R = TypeVar("R")


def handle_exception(
    logger_instance: logging.Logger,
    operation_desc: str,
    input_identifier_key: Optional[str] = None,
    output_identifier_key: Optional[str] = None,
    include_error_type: bool = True,
):
    """
    A decorator for handling exceptions in a consistent way.

    Args:
        logger_instance: The logger to use for logging errors
        operation_desc: Description of the operation (e.g., "downloading PDF content")
        identifier_key: Optional key to extract identifier from kwargs (e.g., "doi")
        output_identifier_key: Optional key to extract from function output dictionary
                              (only applies if function succeeds, not used in error handling)
        include_error_type: Whether to include the error type in the log message

    Returns:
        A decorator that wraps a function with standardized exception handling
    """

    def decorator(func):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                # Execute the original function
                result = await func(*args, **kwargs)

                # If we have a result and output_identifier_key is specified, log the success
                if (
                    result
                    and output_identifier_key
                    and isinstance(result, dict)
                    and output_identifier_key in result
                ):
                    output_id = result[output_identifier_key]
                    logger_instance.info(
                        f"Successfully completed {operation_desc} with {output_identifier_key} {output_id}"
                    )

                return result

            except Exception as e:
                error_type = type(e).__name__

                # Extract identifier if provided
                identifier = ""
                if input_identifier_key and input_identifier_key in kwargs:
                    identifier = (
                        f" for {input_identifier_key} {kwargs[input_identifier_key]}"
                    )

                # Format error message
                error_info = f"({error_type}): {e}" if include_error_type else f"{e}"
                log_message = f"Error {operation_desc}{identifier}: {error_info}"

                # Log the error
                logger_instance.error(log_message)

                # Re-raise with a cleaner message
                raise Exception(f"Error {operation_desc}{identifier}: {e}")

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            try:
                # Execute the original function
                result = func(*args, **kwargs)

                # If we have a result and output_identifier_key is specified, log the success
                if (
                    result
                    and output_identifier_key
                    and isinstance(result, dict)
                    and output_identifier_key in result
                ):
                    output_id = result[output_identifier_key]
                    logger_instance.info(
                        f"Successfully completed {operation_desc} with {output_identifier_key} {output_id}"
                    )

                return result

            except Exception as e:
                error_type = type(e).__name__

                # Extract identifier if provided
                identifier = ""
                if input_identifier_key and input_identifier_key in kwargs:
                    identifier = (
                        f" for {input_identifier_key} {kwargs[input_identifier_key]}"
                    )

                # Format error message
                error_info = f"({error_type}): {e}" if include_error_type else f"{e}"
                log_message = f"Error {operation_desc}{identifier}: {error_info}"

                # Log the error
                logger_instance.error(log_message)

                # Re-raise with a cleaner message
                raise Exception(f"Error {operation_desc}{identifier}: {e}")

        # Return the appropriate wrapper based on whether the function is async or not
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator
