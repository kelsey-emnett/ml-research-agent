import unittest
from unittest.mock import patch, MagicMock
import os

from app.v1.client.openai_chat import OpenAIChat

path = OpenAIChat.__module__


class TestOpenAIChat(unittest.TestCase):
    def setUp(self):
        self.chat_cls = OpenAIChat()
        self.api_key = os.getenv("AZURE_OPENAI_API_KEY")
        self.endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        self.api_version = os.getenv("AZURE_OPENAI_VERSION")
        self.model_name = "gpt-4.1-mini"
        self.max_tokens = 100
        self.temperature = 0.01

    @patch(path + ".AzureOpenAI")
    def test_initialize_openai_client(self, mock_initialize_client):
        client = self.chat_cls.initialize_openai_client()

        mock_initialize_client.assert_called_once_with(
            api_version=self.api_version,
            azure_endpoint=self.endpoint,
            api_key=self.api_key,
        )

        self.assertEqual(client, mock_initialize_client.return_value)

    def test_construct_model_input_normal(self):
        mock_system_message = "hi."
        mock_user_message = "hello."

        expected_output = [
            {"role": "system", "content": "hi."},
            {"role": "user", "content": "hello."},
        ]

        result = self.chat_cls.construct_model_input(
            mock_system_message, mock_user_message
        )

        self.assertEqual(result, expected_output)

    def test_construct_model_input_invalid_inputs(self):
        invalid_inputs = [
            (None, "test"),
            ("test", None),
            ("", "test"),
            ("test", ""),
        ]

        for test_system_message, test_user_message in invalid_inputs:
            with self.assertRaises(ValueError):
                self.chat_cls.construct_model_input(
                    test_system_message, test_user_message
                )

    @patch(path + ".OpenAIChat.construct_model_input")
    @patch(path + ".OpenAIChat.initialize_openai_client")
    def test_chat_normal(self, mock_initialize_client, mock_construct_model_input):
        system_message = "Hello"
        user_message = "How are you?"
        fake_model_input = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message},
        ]
        expected_response = "I am good, how about you?"

        mock_construct_model_input.return_value = fake_model_input

        mock_client = MagicMock()
        mock_initialize_client.return_value = mock_client

        mock_completion = MagicMock()
        mock_completion.choices[0].message.content = expected_response
        mock_client.chat.completions.create.return_value = mock_completion

        result = self.chat_cls.chat(system_message, user_message)

        mock_construct_model_input.assert_called_once_with(system_message, user_message)
        mock_client.chat.completions.create.assert_called_once_with(
            messages=fake_model_input,
            max_completion_tokens=self.max_tokens,
            temperature=self.temperature,
            model=self.model_name,
        )

        self.assertEqual(result, expected_response)

    @patch(path + ".OpenAIChat.initialize_openai_client")
    def test_chat_with_api_error(self, mock_initialize_chat):
        system_message = "Hello"
        user_message = "How are you?"

        mock_client = MagicMock()
        mock_initialize_chat.return_value = mock_client
        mock_client.chat.completions.create.side_effect = Exception("API Error")

        with self.assertRaises(Exception):
            self.chat_cls.chat(system_message, user_message)


if __name__ == "__main__":
    unittest.main()
