import os
from azure.storage.blob import BlobServiceClient, ContentSettings
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)


class AzureBlobStorageClient:
    def __init__(self):
        try:
            load_dotenv()

            # Get connection string from environment variable
            self.connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
            if not self.connection_string:
                raise ValueError(
                    "Missing AZURE_STORAGE_CONNECTION_STRING environment variable"
                )

            self.account_name = os.getenv("STORAGE_ACCOUNT_NAME")
            self.container_name = os.getenv("STORAGE_CONTAINER_NAME")

            # Create the BlobServiceClient
            self.blob_service_client = BlobServiceClient.from_connection_string(
                self.connection_string
            )
            self.container_client = self.blob_service_client.get_container_client(
                self.container_name
            )
        except Exception as e:
            error_type = type(e).__name__
            logger.error(
                f"Error initializing Azure Blob Storage client: ({error_type}): {e}"
            )
            raise Exception(f"Error initializing Azure Blob Storage client: {str(e)}")

    def upload_pdf_from_memory(self, file_content, blob_name):
        """
        Uploads a PDF file from memory to Azure Blob Storage

        Args:
            file_content (bytes): PDF file content
            blob_name (str): Name to use for the blob

        Returns:
            str: URL of the uploaded blob
        """
        try:
            # Create a blob client
            blob_client = self.container_client.get_blob_client(blob_name)

            # Set content settings for PDF
            content_settings = ContentSettings(content_type="application/pdf")

            # Upload the file from memory
            blob_client.upload_blob(
                file_content, overwrite=True, content_settings=content_settings
            )

            # Return the URL to the blob
            return blob_client.url
        except Exception as e:
            error_type = type(e).__name__
            logger.error(
                f"Error uploading PDF to Azure Blob Storage: ({error_type}): {e}"
            )
            raise Exception(f"Error uploading PDF to Azure Blob Storage: {str(e)}")
