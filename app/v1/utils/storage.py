import os
from azure.storage.blob import BlobServiceClient, ContentSettings
from dotenv import load_dotenv


class AzureBlobStorageClient:
    def __init__(self):
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

    def upload_pdf_from_memory(self, file_content, blob_name):
        """
        Uploads a PDF file from memory to Azure Blob Storage

        Args:
            file_content (bytes): PDF file content
            blob_name (str): Name to use for the blob

        Returns:
            str: URL of the uploaded blob
        """
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
