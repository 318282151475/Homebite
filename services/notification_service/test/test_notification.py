import pytest
from unittest.mock import patch
from notification_service.app.kafka.consumer import route_event


@pytest.mark.asyncio
async def test_health_check():
    from httpx import AsyncClient, ASGITransport
    from app.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_user_registered_sends_email():
    with patch("app.kafka.consumer.send_email") as mock_send:
        await route_event("user.registered", {
            "event": "user.registered",
            "email": "test@example.com",
            "full_name": "Test User",
            "user_id": 1,
        })
        mock_send.assert_called_once()
        call_args = mock_send.call_args
        assert call_args[0][0] == "test@example.com"


@pytest.mark.asyncio
async def test_order_created_missing_email_logs_warning():
    # If event missing user_email, should not crash — just log warning
    with patch("app.kafka.consumer.send_email") as mock_send:
        await route_event("order.created", {
            "event": "order.created",
            "order_id": 1,
            "total_amount": 350.0,
            # user_email intentionally missing
        })
        mock_send.assert_not_called()


@pytest.mark.asyncio
async def test_unknown_event_does_not_crash():
    # Unknown event types should be silently ignored
    await route_event("some.unknown.event", {"event": "some.unknown.event"})