from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.sql import func
from typing import List, Optional
from ..models.delivery import Delivery, DeliveryStatus
from ..schemas.delivery import DeliveryCreateRequest


async def create_delivery(db: AsyncSession, data: DeliveryCreateRequest) -> Delivery:
    delivery = Delivery(
        order_id=data.order_id,
        chef_id=data.chef_id,
        user_id=data.user_id,
        delivery_address=data.delivery_address,
        city=data.city,
        pincode=data.pincode,
        estimated_delivery_minutes=data.estimated_delivery_minutes,
        status=DeliveryStatus.PENDING,
    )
    db.add(delivery)
    await db.flush()
    await db.refresh(delivery)
    return delivery


async def get_delivery_by_id(db: AsyncSession, delivery_id: int) -> Optional[Delivery]:
    result = await db.execute(select(Delivery).where(Delivery.id == delivery_id))
    return result.scalar_one_or_none()


async def get_delivery_by_order_id(db: AsyncSession, order_id: int) -> Optional[Delivery]:
    result = await db.execute(select(Delivery).where(Delivery.order_id == order_id))
    return result.scalar_one_or_none()


async def get_deliveries_by_user(db: AsyncSession, user_id: int) -> List[Delivery]:
    """Customer sees their deliveries."""
    result = await db.execute(
        select(Delivery)
        .where(Delivery.user_id == user_id)
        .order_by(Delivery.created_at.desc())
    )
    return result.scalars().all()


async def get_deliveries_by_delivery_person(db: AsyncSession, delivery_person_id: int) -> List[Delivery]:
    """Delivery person sees their assigned deliveries."""
    result = await db.execute(
        select(Delivery)
        .where(Delivery.delivery_person_id == delivery_person_id)
        .order_by(Delivery.created_at.desc())
    )
    return result.scalars().all()


async def get_available_deliveries(db: AsyncSession, city: str) -> List[Delivery]:
    """Returns unassigned deliveries in a city — delivery persons browse these."""
    result = await db.execute(
        select(Delivery)
        .where(
            Delivery.city.ilike(f"%{city}%"),
            Delivery.delivery_person_id == None,
            Delivery.status == DeliveryStatus.PENDING,
        )
        .order_by(Delivery.created_at.asc())
    )
    return result.scalars().all()


async def accept_delivery(
    db: AsyncSession,
    delivery_id: int,
    delivery_person_id: int,
    delivery_person_name: str,
    delivery_person_phone: Optional[str] = None,
) -> Optional[Delivery]:
    """Delivery person accepts an unassigned delivery."""
    result = await db.execute(
        select(Delivery).where(
            Delivery.id == delivery_id,
            Delivery.delivery_person_id == None,   # not already taken
            Delivery.status == DeliveryStatus.PENDING,
        )
    )
    delivery = result.scalar_one_or_none()
    if not delivery:
        return None  # already taken by someone else

    delivery.delivery_person_id = delivery_person_id
    delivery.delivery_person_name = delivery_person_name
    delivery.delivery_person_phone = delivery_person_phone
    delivery.status = DeliveryStatus.ACCEPTED
    delivery.accepted_at = func.now()
    await db.flush()
    await db.refresh(delivery)
    return delivery


async def update_delivery_status(
    db: AsyncSession,
    delivery_id: int,
    new_status: DeliveryStatus,
    delivery_person_name: Optional[str] = None,
    delivery_person_phone: Optional[str] = None,
) -> Optional[Delivery]:
    delivery = await get_delivery_by_id(db, delivery_id)
    if not delivery:
        return None

    delivery.status = new_status

    if new_status == DeliveryStatus.PICKED_UP:
        delivery.picked_up_at = func.now()
        if delivery_person_name:
            delivery.delivery_person_name = delivery_person_name
        if delivery_person_phone:
            delivery.delivery_person_phone = delivery_person_phone

    if new_status == DeliveryStatus.DELIVERED:
        delivery.delivered_at = func.now()

    await db.flush()
    await db.refresh(delivery)
    return delivery