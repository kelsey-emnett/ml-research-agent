from fastapi.testclient import TestClient
from main import app
from unittest.mock import patch

client = TestClient(app)


def test_post_chat_success():
    system_message = "Hello."
    user_message = "How are you?"
    expected_response = "I am good."

    with patch("app.v1.client.openai_chat.OpenAIChat.chat") as mock_chat:
        mock_chat.return_value = expected_response

        response = client.post(
            "/api/v1/chat/",
            json={"system_message": system_message, "user_message": user_message},
        )

        assert response.status_code == 200
        assert response.json()["response"] == expected_response
        assert "request_id" in response.json()
        assert "timestamp" in response.json()
        mock_chat.assert_called_once_with(system_message, user_message)


def test_post_chat_error():
    system_message = "Hello."
    user_message = "How are you?"
    expected_response = "I am good."
    error_message = "OpenAI API Error: Something went wrong."

    with patch("app.v1.client.openai_chat.OpenAIChat.chat") as mock_chat:
        mock_chat.return_value = expected_response

        mock_chat.side_effect = Exception(error_message)

        response = client.post(
            "/api/v1/chat/",
            json={"system_message": system_message, "user_message": user_message},
        )

        assert response.status_code == 500
        assert (
            response.json()["detail"]
            == f"Error processing chat request: {error_message}"
        )
        mock_chat.assert_called_once_with(system_message, user_message)


def test_post_chat_missing_parameter():
    system_message = "Hello."

    with patch("app.v1.client.openai_chat.OpenAIChat.chat"):
        response = client.post("/api/v1/chat/", json={"system_message": system_message})

        assert response.status_code == 422
