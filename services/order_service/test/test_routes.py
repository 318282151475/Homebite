import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, patch
from app.main import app
from order_service.app.models.order import OrderStatus


@pytest.mark.asyncio
async def test_health_check():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


@pytest.mark.asyncio
async def test_place_order_success():
    mock_order = AsyncMock()
    mock_order.id = 1
    mock_order.user_id = 5
    mock_order.chef_id = None
    mock_order.status = OrderStatus.PENDING
    mock_order.items = [{"name": "Dal Makhani", "qty": 2, "price": 180.0}]
    mock_order.total_amount = 360.0
    mock_order.delivery_address = "123 MG Road"
    mock_order.city = "Pune"
    mock_order.pincode = "411001"
    mock_order.special_instructions = None
    mock_order.created_at = "2024-01-01T00:00:00"
    mock_order.updated_at = "2024-01-01T00:00:00"
    mock_order.delivered_at = None

    with patch("app.api.v1.routes.create_order", return_value=mock_order), \
         patch("app.api.v1.routes.publish_event", return_value=None):

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/api/v1/orders/", json={
                "user_id": 5,
                "items": [{"name": "Dal Makhani", "qty": 2, "price": 180.0}],
                "delivery_address": "123 MG Road",
                "city": "Pune",
                "pincode": "411001",
            })

    assert response.status_code == 201
    assert response.json()["status"] == "pending"
    assert response.json()["total_amount"] == 360.0


@pytest.mark.asyncio
async def test_place_order_empty_items_rejected():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/api/v1/orders/", json={
            "user_id": 5,
            "items": [],        # empty items — must be rejected
            "delivery_address": "123 MG Road",
            "city": "Pune",
            "pincode": "411001",
        })

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_place_order_invalid_pincode():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/api/v1/orders/", json={
            "user_id": 5,
            "items": [{"name": "Dal Makhani", "qty": 1, "price": 180.0}],
            "delivery_address": "123 MG Road",
            "city": "Pune",
            "pincode": "123",   # invalid pincode
        })

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_place_order_zero_quantity_rejected():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/api/v1/orders/", json={
            "user_id": 5,
            "items": [{"name": "Dal Makhani", "qty": 0, "price": 180.0}],
            "delivery_address": "123 MG Road",
            "city": "Pune",
            "pincode": "411001",
        })

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_order_success():
    mock_order = AsyncMock()
    mock_order.id = 1
    mock_order.user_id = 5
    mock_order.chef_id = 3
    mock_order.status = OrderStatus.CHEF_ASSIGNED
    mock_order.items = [{"name": "Dal Makhani", "qty": 2, "price": 180.0}]
    mock_order.total_amount = 360.0
    mock_order.delivery_address = "123 MG Road"
    mock_order.city = "Pune"
    mock_order.pincode = "411001"
    mock_order.special_instructions = None
    mock_order.created_at = "2024-01-01T00:00:00"
    mock_order.updated_at = "2024-01-01T00:00:00"
    mock_order.delivered_at = None

    with patch("app.api.v1.routes.get_order_by_id", return_value=mock_order):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/orders/1")

    assert response.status_code == 200
    assert response.json()["id"] == 1
    assert response.json()["status"] == "chef_assigned"


@pytest.mark.asyncio
async def test_get_order_not_found():
    with patch("app.api.v1.routes.get_order_by_id", return_value=None):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/orders/999")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_user_orders():
    mock_order = AsyncMock()
    mock_order.id = 1
    mock_order.user_id = 5
    mock_order.chef_id = None
    mock_order.status = OrderStatus.PENDING
    mock_order.items = [{"name": "Dal Makhani", "qty": 1, "price": 180.0}]
    mock_order.total_amount = 180.0
    mock_order.delivery_address = "123 MG Road"
    mock_order.city = "Pune"
    mock_order.pincode = "411001"
    mock_order.special_instructions = None
    mock_order.created_at = "2024-01-01T00:00:00"
    mock_order.updated_at = "2024-01-01T00:00:00"
    mock_order.delivered_at = None

    with patch("app.api.v1.routes.get_orders_by_user", return_value=[mock_order]):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/orders/user/5")

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["user_id"] == 5


@pytest.mark.asyncio
async def test_cancel_order_success():
    mock_order = AsyncMock()
    mock_order.id = 1
    mock_order.user_id = 5
    mock_order.chef_id = None
    mock_order.status = OrderStatus.CANCELLED
    mock_order.items = [{"name": "Dal Makhani", "qty": 1, "price": 180.0}]
    mock_order.total_amount = 180.0
    mock_order.delivery_address = "123 MG Road"
    mock_order.city = "Pune"
    mock_order.pincode = "411001"
    mock_order.special_instructions = None
    mock_order.created_at = "2024-01-01T00:00:00"
    mock_order.updated_at = "2024-01-01T00:00:00"
    mock_order.delivered_at = None

    with patch("app.api.v1.routes.cancel_order", return_value=mock_order):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/api/v1/orders/1/cancel")

    assert response.status_code == 200
    assert response.json()["status"] == "cancelled"


@pytest.mark.asyncio
async def test_cancel_order_not_allowed():
    # cancel_order returns None when order cannot be cancelled
    # e.g. order is already delivered or out for delivery
    with patch("app.api.v1.routes.cancel_order", return_value=None):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/api/v1/orders/1/cancel")

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_kafka_event_published_on_order_creation():
    # verify that kafka publish_event is called when order is placed
    # this is important — order_service MUST publish event for async flow to work
    mock_order = AsyncMock()
    mock_order.id = 1
    mock_order.user_id = 5
    mock_order.chef_id = None
    mock_order.status = OrderStatus.PENDING
    mock_order.items = [{"name": "Dal Makhani", "qty": 1, "price": 180.0}]
    mock_order.total_amount = 180.0
    mock_order.delivery_address = "123 MG Road"
    mock_order.city = "Pune"
    mock_order.pincode = "411001"
    mock_order.special_instructions = None
    mock_order.created_at = "2024-01-01T00:00:00"
    mock_order.updated_at = "2024-01-01T00:00:00"
    mock_order.delivered_at = None

    with patch("app.api.v1.routes.create_order", return_value=mock_order), \
         patch("app.api.v1.routes.publish_event", return_value=None) as mock_publish:

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            await client.post("/api/v1/orders/", json={
                "user_id": 5,
                "items": [{"name": "Dal Makhani", "qty": 1, "price": 180.0}],
                "delivery_address": "123 MG Road",
                "city": "Pune",
                "pincode": "411001",
            })

    # publish_event must have been called exactly once
    mock_publish.assert_called_once()

    # verify the correct topic was used
    call_args = mock_publish.call_args
    assert call_args.kwargs["topic"] == "order.created" or call_args.args[0] == "order.created"