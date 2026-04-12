import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, patch
from app.main import app
from delivery_service.app.models.delivery import DeliveryStatus


@pytest.mark.asyncio
async def test_health_check():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


@pytest.mark.asyncio
async def test_get_delivery_not_found():
    with patch("app.api.v1.routes.get_delivery_by_id", return_value=None):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/deliveries/999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_invalid_status_transition():
    mock_delivery = AsyncMock()
    mock_delivery.id = 1
    mock_delivery.order_id = 1
    mock_delivery.chef_id = 1
    mock_delivery.user_id = 1
    mock_delivery.status = DeliveryStatus.DELIVERED  # terminal state
    mock_delivery.delivery_address = "123 Main St"
    mock_delivery.city = "Pune"
    mock_delivery.pincode = "411001"
    mock_delivery.delivery_person_name = None
    mock_delivery.delivery_person_phone = None
    mock_delivery.estimated_delivery_minutes = 45
    mock_delivery.created_at = "2024-01-01T00:00:00"
    mock_delivery.updated_at = "2024-01-01T00:00:00"
    mock_delivery.picked_up_at = None
    mock_delivery.delivered_at = None

    with patch("app.api.v1.routes.get_delivery_by_id", return_value=mock_delivery):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.patch("/api/v1/deliveries/1/status", json={
                "status": "picked_up"  # cannot go back from DELIVERED
            })
    assert response.status_code == 400