import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, patch
from app.main import app


@pytest.mark.asyncio
async def test_health_check():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


@pytest.mark.asyncio
async def test_register_success():
    mock_user = AsyncMock()
    mock_user.id = 1
    mock_user.full_name = "Test User"
    mock_user.email = "test@example.com"
    mock_user.phone = None
    mock_user.role = "customer"
    mock_user.is_active = True
    mock_user.is_verified = False
    mock_user.created_at = "2024-01-01T00:00:00"

    with patch("app.api.v1.routes.user_crud.get_user_by_email", return_value=None), \
         patch("app.api.v1.routes.user_crud.get_user_by_phone", return_value=None), \
         patch("app.api.v1.routes.user_crud.create_user", return_value=mock_user), \
         patch("app.api.v1.routes.publish_event", return_value=None):

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/api/v1/users/register", json={
                "full_name": "Test User",
                "email": "test@example.com",
                "password": "SecurePass1!",
            })

    assert response.status_code == 201
    assert response.json()["email"] == "test@example.com"


@pytest.mark.asyncio
async def test_register_duplicate_email():
    mock_existing = AsyncMock()
    with patch("app.api.v1.routes.user_crud.get_user_by_email", return_value=mock_existing):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/api/v1/users/register", json={
                "full_name": "Test User",
                "email": "existing@example.com",
                "password": "SecurePass1!",
            })
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_login_wrong_credentials():
    with patch("app.api.v1.routes.user_crud.get_user_by_email", return_value=None):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/api/v1/users/login", json={
                "email": "nobody@example.com",
                "password": "WrongPass1!",
            })
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_weak_password_rejected():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/api/v1/users/register", json={
            "full_name": "Test User",
            "email": "test@example.com",
            "password": "weak",
        })
    assert response.status_code == 422