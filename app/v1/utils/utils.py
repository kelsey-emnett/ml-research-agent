import aiohttp
import ssl
import string


def create_ssl_context():
    # Create a custom SSL context that doesn't verify certificates
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    # Configure the client session with the SSL context
    connector = aiohttp.TCPConnector(ssl=ssl_context)

    return connector


def filter_valid_results(results):
    return [
        result for result in results if result and not isinstance(result, Exception)
    ]


def create_file_name(title):
    remove_punctuation = str.maketrans("", "", string.punctuation)

    return (
        title.translate(remove_punctuation).lower().replace(" ", "_").lower()[0:40]
        + ".pdf"
    )
