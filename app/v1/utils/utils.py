import aiohttp
import ssl
import string
import logging

logger = logging.getLogger(__name__)


def create_ssl_context():
    try:
        # Create a custom SSL context that doesn't verify certificates
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE

        # Configure the client session with the SSL context
        connector = aiohttp.TCPConnector(ssl=ssl_context)

        return connector
    except Exception as e:
        error_type = type(e).__name__
        logger.error(f"Error creating SSL context: ({error_type}): {e}")
        raise Exception(f"Error creating SSL context: {e}")


def filter_valid_results(results):
    try:
        return [
            result for result in results if result and not isinstance(result, Exception)
        ]
    except Exception as e:
        raise Exception(f"Error filtering valid results: {e}")


def create_file_name(title):
    try:
        remove_punctuation = str.maketrans("", "", string.punctuation)

        return (
            title.translate(remove_punctuation).lower().replace(" ", "_").lower()[0:40]
            + ".pdf"
        )
    except Exception as e:
        raise Exception(f"Error creating file name: {e}")
