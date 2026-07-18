from unittest.mock import AsyncMock, patch
import pytest
from fastapi.testclient import TestClient

@pytest.fixture
def client():
    from api.main import app
    return TestClient(app)

class TestChatAPI:
    @patch("api.routers.chat.process_chat_message")
    def test_send_message(self, mock_chat, client):
        mock_chat.return_value = {"reply": "Info here...", "sources": []}
        response = client.post("/api/chat/message", json={
            "notebook_id": "nb-1", "message": "Tell me about RAG", "context": True
        })
        assert response.status_code == 200
        assert "reply" in response.json()

    def test_send_empty_message(self, client):
        response = client.post("/api/chat/message", json={"notebook_id": "nb-1", "message": ""})
        assert response.status_code == 422
