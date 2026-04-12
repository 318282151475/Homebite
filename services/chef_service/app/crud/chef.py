from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from typing import Optional, List
from ..models.chef import Chef, ChefStatus
from ..schemas.chef import ChefCreateRequest


async def get_chef_by_id(db: AsyncSession, chef_id: int) -> Optional[Chef]:
    result = await db.execute(select(Chef).where(Chef.id == chef_id))
    return result.scalar_one_or_none()


async def get_chef_by_user_id(db: AsyncSession, user_id: int) -> Optional[Chef]:
    result = await db.execute(select(Chef).where(Chef.user_id == user_id))
    return result.scalar_one_or_none()


async def get_available_chefs(db: AsyncSession, city: str) -> List[Chef]:
    result = await db.execute(
        select(Chef).where(
            Chef.status == ChefStatus.AVAILABLE,
            Chef.is_active == True,
            Chef.city == city,
        )
    )
    return result.scalars().all()


async def create_chef(db: AsyncSession, data: ChefCreateRequest) -> Chef:
    chef = Chef(**data.model_dump())
    db.add(chef)
    await db.flush()
    await db.refresh(chef)
    return chef


async def update_chef_status(db: AsyncSession, chef_id: int, status: ChefStatus) -> Optional[Chef]:
    await db.execute(
        update(Chef)
        .where(Chef.id == chef_id)
        .values(status=status)
    )
    return await get_chef_by_id(db, chef_id)


async def assign_chef_to_order(db: AsyncSession, chef_id: int) -> Optional[Chef]:
    """
    Atomically marks chef as BUSY.
    Called when order.created event is consumed from Kafka.
    """
    chef = await get_chef_by_id(db, chef_id)
    if not chef or chef.status != ChefStatus.AVAILABLE:
        return None
    chef.status = ChefStatus.BUSY
    chef.total_orders += 1
    await db.flush()
    await db.refresh(chef)
    return chef


async def release_chef(db: AsyncSession, chef_id: int) -> Optional[Chef]:
    """
    Marks chef as AVAILABLE again after order is delivered.
    Called when delivery_service.completed event is consumed from Kafka.
    """
    return await update_chef_status(db, chef_id, ChefStatus.AVAILABLE)