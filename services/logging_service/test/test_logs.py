import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, patch
from app.main import app
from app.kafka.consumer import persist_event_log


@pytest.mark.asyncio
async def test_health_check():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_query_logs_empty():
    with patch("app.api.v1.routes.get_logs", return_value=[]):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/logs/")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_get_log_not_found():
    with patch("app.api.v1.routes.get_log_by_id", return_value=None):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/logs/999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_failure_event_stored_as_warning():
    """
    chef.assignment_failed must be stored with WARNING level
    not INFO level
    """
    mock_log = AsyncMock()

    with patch("app.kafka.consumer.AsyncSessionLocal") as mock_session_factory:
        mock_db = AsyncMock()
        mock_session_factory.return_value.__aenter__.return_value = mock_db

        with patch("app.kafka.consumer.create_log", return_value=mock_log) as mock_create:
            await persist_event_log(
                "chef.assignment_failed",
                {"event": "chef.assignment_failed", "order_id": 1}
            )

            call_kwargs = mock_create.call_args.kwargs
            assert call_kwargs["level"].value == "warning"


@pytest.mark.asyncio
async def test_normal_event_stored_as_info():
    mock_log = AsyncMock()

    with patch("app.kafka.consumer.AsyncSessionLocal") as mock_session_factory:
        mock_db = AsyncMock()
        mock_session_factory.return_value.__aenter__.return_value = mock_db

        with patch("app.kafka.consumer.create_log", return_value=mock_log) as mock_create:
            await persist_event_log(
                "order.created",
                {"event": "order.created", "order_id": 1, "user_id": 5}
            )

            call_kwargs = mock_create.call_args.kwargs
            assert call_kwargs["level"].value == "info"
            assert call_kwargs["order_id"] == 1
            assert call_kwargs["user_id"] == 5