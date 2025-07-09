import unittest
import ssl
from unittest.mock import patch, MagicMock
from app.v1.utils.utils import create_ssl_context
from app.v1.utils.utils import create_file_name


class TestCreateSSLContext(unittest.TestCase):
    @patch("aiohttp.TCPConnector")
    def test_create_ssl_context_returns_connector(self, mock_connector):
        """Test that create_ssl_context returns an aiohttp TCPConnector."""
        # Set up the mock
        mock_instance = MagicMock()
        mock_connector.return_value = mock_instance

        # Call the function
        connector = create_ssl_context()

        # Check that the function returns what we expect
        self.assertEqual(connector, mock_instance)

        # Verify TCPConnector was created with SSL context
        args, kwargs = mock_connector.call_args
        self.assertIn("ssl", kwargs)
        self.assertIsInstance(kwargs["ssl"], ssl.SSLContext)

    @patch("aiohttp.TCPConnector")
    def test_ssl_context_has_correct_settings(self, mock_connector):
        """Test that the SSL context has the correct security settings."""
        # Call the function
        create_ssl_context()

        # Extract the SSL context from the connector constructor call
        args, kwargs = mock_connector.call_args
        ssl_context = kwargs["ssl"]

        # Verify SSL context settings
        self.assertIsInstance(ssl_context, ssl.SSLContext)
        self.assertFalse(ssl_context.check_hostname)
        self.assertEqual(ssl_context.verify_mode, ssl.CERT_NONE)

    @patch("ssl.create_default_context")
    @patch("aiohttp.TCPConnector")
    def test_create_ssl_context_calls_expected_functions(
        self, mock_connector, mock_ssl_context
    ):
        """Test that create_ssl_context calls the expected functions with correct parameters."""
        # Set up mocks
        mock_ssl_instance = MagicMock()
        mock_ssl_context.return_value = mock_ssl_instance
        mock_connector.return_value = "mocked_connector"

        # Call the function
        result = create_ssl_context()

        # Verify ssl.create_default_context was called
        mock_ssl_context.assert_called_once()

        # Verify properties were set on the SSL context
        self.assertEqual(mock_ssl_instance.check_hostname, False)
        self.assertEqual(mock_ssl_instance.verify_mode, ssl.CERT_NONE)

        # Verify TCPConnector was created with the SSL context
        mock_connector.assert_called_once_with(ssl=mock_ssl_instance)

        # Verify the function returned the connector
        self.assertEqual(result, "mocked_connector")

    @patch("ssl.create_default_context")
    def test_create_ssl_context_error_handling(self, mock_ssl_context):
        """Test that the function properly handles errors."""
        # Set up mock to raise an exception
        mock_ssl_context.side_effect = Exception("Test error")

        # Verify the exception is properly handled and re-raised
        with self.assertRaises(Exception) as context:
            create_ssl_context()

        # Check the error message
        self.assertIn("Error creating SSL context", str(context.exception))


class TestCreateFileName(unittest.TestCase):
    def test_create_file_name_returns_correct_filename(self):
        """Test that create_file_name returns the correct filename."""
        title = "This is a test title*"
        expected_filename = "this_is_a_test_title.pdf"

        actual_filename = create_file_name(title)

        self.assertEqual(actual_filename, expected_filename)


if __name__ == "__main__":
    unittest.main()
