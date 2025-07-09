import unittest
from unittest.mock import patch, MagicMock
from azure.storage.blob import ContentSettings
from app.v1.utils.storage import AzureBlobStorageClient


class TestAzureBlobStorageClient(unittest.TestCase):
    """Test cases for AzureBlobStorageClient class"""

    def setUp(self):
        """Set up test environment before each test"""
        # Define environment variables for testing
        self.env_patcher = patch.dict(
            "os.environ",
            {
                "AZURE_STORAGE_CONNECTION_STRING": "test_connection_string",
                "STORAGE_ACCOUNT_NAME": "test_account_name",
                "STORAGE_CONTAINER_NAME": "test_container_name",
            },
        )
        self.env_patcher.start()

        # Create patchers for external dependencies
        self.blob_service_client_patcher = patch(
            "azure.storage.blob.BlobServiceClient.from_connection_string"
        )
        self.mock_blob_service_client = self.blob_service_client_patcher.start()

        # Setup the mock structure (BlobServiceClient -> ContainerClient -> BlobClient)
        self.mock_blob_service = MagicMock()
        self.mock_container_client = MagicMock()
        self.mock_blob_client = MagicMock()

        # Configure return values for the mock chain
        self.mock_blob_service_client.return_value = self.mock_blob_service
        self.mock_blob_service.get_container_client.return_value = (
            self.mock_container_client
        )
        self.mock_container_client.get_blob_client.return_value = self.mock_blob_client

        # Mock load_dotenv to do nothing
        self.dotenv_patcher = patch("app.v1.utils.storage.load_dotenv")
        self.mock_dotenv = self.dotenv_patcher.start()

    def tearDown(self):
        """Clean up after each test"""
        # Stop all patchers
        self.env_patcher.stop()
        self.blob_service_client_patcher.stop()
        self.dotenv_patcher.stop()

    def test_init_success(self):
        """Test successful initialization of AzureBlobStorageClient"""
        # Create an instance of the client
        client = AzureBlobStorageClient()

        # Verify BlobServiceClient was created with correct connection string
        self.mock_blob_service_client.assert_called_once_with("test_connection_string")

        # Verify container client was retrieved with correct container name
        self.mock_blob_service.get_container_client.assert_called_once_with(
            "test_container_name"
        )

        # Verify attributes were set correctly
        self.assertEqual(client.connection_string, "test_connection_string")
        self.assertEqual(client.account_name, "test_account_name")
        self.assertEqual(client.container_name, "test_container_name")
        self.assertEqual(client.blob_service_client, self.mock_blob_service)
        self.assertEqual(client.container_client, self.mock_container_client)

    def test_init_missing_connection_string(self):
        """Test initialization fails when connection string is missing"""
        # Remove the connection string from environment
        with patch.dict("os.environ", {"AZURE_STORAGE_CONNECTION_STRING": ""}):
            # Verify exception is raised
            with self.assertRaises(Exception) as context:
                AzureBlobStorageClient()

            # Verify the error message
            self.assertIn(
                "Missing AZURE_STORAGE_CONNECTION_STRING", str(context.exception)
            )

    def test_upload_pdf_from_memory(self):
        """Test uploading PDF content to Azure Blob Storage"""
        # Create a client instance
        client = AzureBlobStorageClient()

        # Set up test data
        test_content = b"test PDF content"
        test_blob_name = "test_document.pdf"

        # Configure mock blob client to return a specific URL
        self.mock_blob_client.url = (
            "https://test.blob.core.windows.net/test_container_name/test_document.pdf"
        )

        # Call the method
        result = client.upload_pdf_from_memory(test_content, test_blob_name)

        # Verify blob client was created with correct blob name
        self.mock_container_client.get_blob_client.assert_called_once_with(
            test_blob_name
        )

        # Verify upload_blob was called with correct parameters
        self.mock_blob_client.upload_blob.assert_called_once()

        # Get the call arguments
        args, kwargs = self.mock_blob_client.upload_blob.call_args

        # Verify content was passed correctly
        self.assertEqual(args[0], test_content)

        # Verify overwrite parameter
        self.assertTrue(kwargs["overwrite"])

        # Verify content_settings is a ContentSettings object with PDF content type
        self.assertIsInstance(kwargs["content_settings"], ContentSettings)
        self.assertEqual(kwargs["content_settings"].content_type, "application/pdf")

        # Verify correct URL is returned
        self.assertEqual(
            result,
            "https://test.blob.core.windows.net/test_container_name/test_document.pdf",
        )

    def test_upload_pdf_from_memory_error(self):
        """Test error handling when uploading PDF fails"""
        # Create a client instance
        client = AzureBlobStorageClient()

        # Configure mock to raise an exception
        self.mock_blob_client.upload_blob.side_effect = Exception("Upload failed")

        # Set up test data
        test_content = b"test PDF content"
        test_blob_name = "test_document.pdf"

        # Verify exception is handled by the decorator
        with self.assertRaises(Exception) as context:
            client.upload_pdf_from_memory(test_content, test_blob_name)

        # Verify error message contains our decorator's additional context
        self.assertIn(
            "Error uploading PDF to Azure Blob Storage", str(context.exception)
        )


if __name__ == "__main__":
    unittest.main()
