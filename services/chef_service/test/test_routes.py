import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, patch
from app.main import app
from app.models.chef import ChefStatus, CuisineType


@pytest.mark.asyncio
async def test_health_check():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


@pytest.mark.asyncio
async def test_register_chef_success():
    mock_chef = AsyncMock()
    mock_chef.id = 1
    mock_chef.user_id = 10
    mock_chef.full_name = "Priya Sharma"
    mock_chef.bio = "Expert in North Indian cuisine"
    mock_chef.cuisine_type = CuisineType.NORTH_INDIAN
    mock_chef.experience_years = 5
    mock_chef.rating = 0.0
    mock_chef.total_orders = 0
    mock_chef.status = ChefStatus.OFFLINE
    mock_chef.is_active = True
    mock_chef.city = "Pune"
    mock_chef.pincode = "411001"
    mock_chef.created_at = "2024-01-01T00:00:00"

    with patch("app.api.v1.routes.get_chef_by_user_id", return_value=None), \
         patch("app.api.v1.routes.create_chef", return_value=mock_chef):

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/api/v1/chefs/", json={
                "user_id": 10,
                "full_name": "Priya Sharma",
                "bio": "Expert in North Indian cuisine",
                "cuisine_type": "north_indian",
                "experience_years": 5,
                "city": "Pune",
                "pincode": "411001",
            })

    assert response.status_code == 201
    assert response.json()["full_name"] == "Priya Sharma"
    assert response.json()["city"] == "Pune"


@pytest.mark.asyncio
async def test_register_chef_duplicate():
    mock_existing = AsyncMock()

    with patch("app.api.v1.routes.get_chef_by_user_id", return_value=mock_existing):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/api/v1/chefs/", json={
                "user_id": 10,
                "full_name": "Priya Sharma",
                "cuisine_type": "north_indian",
                "city": "Pune",
                "pincode": "411001",
            })

    assert response.status_code == 409


@pytest.mark.asyncio
async def test_get_chef_success():
    mock_chef = AsyncMock()
    mock_chef.id = 1
    mock_chef.user_id = 10
    mock_chef.full_name = "Priya Sharma"
    mock_chef.bio = None
    mock_chef.cuisine_type = CuisineType.NORTH_INDIAN
    mock_chef.experience_years = 5
    mock_chef.rating = 4.5
    mock_chef.total_orders = 20
    mock_chef.status = ChefStatus.AVAILABLE
    mock_chef.is_active = True
    mock_chef.city = "Pune"
    mock_chef.pincode = "411001"
    mock_chef.created_at = "2024-01-01T00:00:00"

    with patch("app.api.v1.routes.get_chef_by_id", return_value=mock_chef):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/chefs/1")

    assert response.status_code == 200
    assert response.json()["id"] == 1
    assert response.json()["status"] == "available"


@pytest.mark.asyncio
async def test_get_chef_not_found():
    with patch("app.api.v1.routes.get_chef_by_id", return_value=None):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/chefs/999")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_available_chefs():
    mock_chef_1 = AsyncMock()
    mock_chef_1.id = 1
    mock_chef_1.user_id = 10
    mock_chef_1.full_name = "Priya Sharma"
    mock_chef_1.bio = None
    mock_chef_1.cuisine_type = CuisineType.NORTH_INDIAN
    mock_chef_1.experience_years = 5
    mock_chef_1.rating = 4.5
    mock_chef_1.total_orders = 20
    mock_chef_1.status = ChefStatus.AVAILABLE
    mock_chef_1.is_active = True
    mock_chef_1.city = "Pune"
    mock_chef_1.pincode = "411001"
    mock_chef_1.created_at = "2024-01-01T00:00:00"

    mock_chef_2 = AsyncMock()
    mock_chef_2.id = 2
    mock_chef_2.user_id = 11
    mock_chef_2.full_name = "Rahul Verma"
    mock_chef_2.bio = None
    mock_chef_2.cuisine_type = CuisineType.SOUTH_INDIAN
    mock_chef_2.experience_years = 3
    mock_chef_2.rating = 4.2
    mock_chef_2.total_orders = 15
    mock_chef_2.status = ChefStatus.AVAILABLE
    mock_chef_2.is_active = True
    mock_chef_2.city = "Pune"
    mock_chef_2.pincode = "411002"
    mock_chef_2.created_at = "2024-01-01T00:00:00"

    with patch("app.api.v1.routes.get_available_chefs", return_value=[mock_chef_1, mock_chef_2]):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/chefs/available/Pune")

    assert response.status_code == 200
    assert len(response.json()) == 2


@pytest.mark.asyncio
async def test_update_chef_status_success():
    mock_chef = AsyncMock()
    mock_chef.id = 1
    mock_chef.user_id = 10
    mock_chef.full_name = "Priya Sharma"
    mock_chef.bio = None
    mock_chef.cuisine_type = CuisineType.NORTH_INDIAN
    mock_chef.experience_years = 5
    mock_chef.rating = 4.5
    mock_chef.total_orders = 20
    mock_chef.status = ChefStatus.AVAILABLE
    mock_chef.is_active = True
    mock_chef.city = "Pune"
    mock_chef.pincode = "411001"
    mock_chef.created_at = "2024-01-01T00:00:00"

    with patch("app.api.v1.routes.update_chef_status", return_value=mock_chef):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.patch("/api/v1/chefs/1/status", json={
                "status": "available"
            })

    assert response.status_code == 200
    assert response.json()["status"] == "available"


@pytest.mark.asyncio
async def test_update_chef_status_not_found():
    with patch("app.api.v1.routes.update_chef_status", return_value=None):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.patch("/api/v1/chefs/999/status", json={
                "status": "available"
            })

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_invalid_pincode_rejected():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/api/v1/chefs/", json={
            "user_id": 10,
            "full_name": "Priya Sharma",
            "cuisine_type": "north_indian",
            "city": "Pune",
            "pincode": "123",    # invalid — must be 6 digits
        })

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_negative_experience_rejected():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/api/v1/chefs/", json={
            "user_id": 10,
            "full_name": "Priya Sharma",
            "cuisine_type": "north_indian",
            "city": "Pune",
            "pincode": "411001",
            "experience_years": -1,    # invalid
        })

    assert response.status_code == 422