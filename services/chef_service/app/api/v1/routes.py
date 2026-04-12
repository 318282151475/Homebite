from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.database import get_db
from ...schemas.chef import ChefCreateRequest, ChefStatusUpdateRequest, ChefResponse
from ...crud.chef import get_chef_by_id, get_chef_by_user_id, get_available_chefs, create_chef, update_chef_status
from ...core.exceptions import ChefNotFoundException, ChefAlreadyExistsException

router = APIRouter(prefix="/api/v1/chefs", tags=["chefs"])


@router.post("/", response_model=ChefResponse, status_code=status.HTTP_201_CREATED)
async def register_chef(data: ChefCreateRequest, db: AsyncSession = Depends(get_db)):
    if await get_chef_by_user_id(db, data.user_id):
        raise ChefAlreadyExistsException()
    return await create_chef(db, data)


@router.get("/{chef_id}", response_model=ChefResponse)
async def get_chef(chef_id: int, db: AsyncSession = Depends(get_db)):
    chef = await get_chef_by_id(db, chef_id)
    if not chef:
        raise ChefNotFoundException()
    return chef

@router.get("/available/{city}", response_model=List[ChefResponse])
async def list_available_chefs(city: str, db: AsyncSession = Depends(get_db)):
    return await get_available_chefs(db, city)


@router.patch("/{chef_id}/status", response_model=ChefResponse)
async def update_status(
    chef_id: int,
    data: ChefStatusUpdateRequest,
    db: AsyncSession = Depends(get_db),
):
    chef = await update_chef_status(db, chef_id, data.status)
    if not chef:
        raise ChefNotFoundException()
    return chef


@router.get("/health", include_in_schema=False)
async def health():
    return {"status": "healthy", "service": "chef_service"}