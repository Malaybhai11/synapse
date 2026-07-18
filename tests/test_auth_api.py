from unittest.mock import AsyncMock, patch
import pytest
from fastapi.testclient import TestClient

@pytest.fixture
def client():
    from api.main import app
    return TestClient(app)

class TestAuthAPI:
    @patch("api.routers.auth.login_user")
    def test_login_success(self, mock_login, client):
        mock_login.return_value = {"token": "test-token", "user_id": "usr-1", "email": "test@example.com"}
        response = client.post("/api/auth/login", json={"email": "test@example.com", "password": "password123"})
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert data["user_id"] == "usr-1"

    @patch("api.routers.auth.login_user")
    def test_login_invalid_credentials(self, mock_login, client):
        mock_login.side_effect = Exception("Invalid credentials")
        response = client.post("/api/auth/login", json={"email": "test@example.com", "password": "wrong"})
        assert response.status_code == 401

    def test_login_missing_email(self, client):
        response = client.post("/api/auth/login", json={"password": "password123"})
        assert response.status_code == 422
