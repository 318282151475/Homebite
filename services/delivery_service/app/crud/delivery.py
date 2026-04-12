from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, List
from datetime import datetime, timezone
from delivery_service.app.models.delivery import Delivery, DeliveryStatus
from delivery_service.app.schemas.delivery import DeliveryCreateRequest


async def get_delivery_by_id(db: AsyncSession, delivery_id: int) -> Optional[Delivery]:
    result = await db.execute(select(Delivery).where(Delivery.id == delivery_id))
    return result.scalar_one_or_none()


async def get_delivery_by_order_id(db: AsyncSession, order_id: int) -> Optional[Delivery]:
    result = await db.execute(select(Delivery).where(Delivery.order_id == order_id))
    return result.scalar_one_or_none()


async def get_deliveries_by_user(db: AsyncSession, user_id: int) -> List[Delivery]:
    result = await db.execute(
        select(Delivery)
        .where(Delivery.user_id == user_id)
        .order_by(Delivery.created_at.desc())
    )
    return result.scalars().all()


async def create_delivery(db: AsyncSession, data: DeliveryCreateRequest) -> Delivery:
    delivery = Delivery(
        order_id=data.order_id,
        chef_id=data.chef_id,
        user_id=data.user_id,
        delivery_address=data.delivery_address,
        city=data.city,
        pincode=data.pincode,
        status=DeliveryStatus.PENDING,
    )
    db.add(delivery)
    await db.flush()
    await db.refresh(delivery)
    return delivery


async def update_delivery_status(
    db: AsyncSession,
    delivery_id: int,
    status: DeliveryStatus,
    delivery_person_name: Optional[str] = None,
    delivery_person_phone: Optional[str] = None,
) -> Optional[Delivery]:
    delivery = await get_delivery_by_id(db, delivery_id)
    if not delivery:
        return None

    delivery.status = status

    if delivery_person_name:
        delivery.delivery_person_name = delivery_person_name
    if delivery_person_phone:
        delivery.delivery_person_phone = delivery_person_phone

    # stamp exact time for each transition
    if status == DeliveryStatus.PICKED_UP:
        delivery.picked_up_at = datetime.now(timezone.utc)
    elif status == DeliveryStatus.DELIVERED:
        delivery.delivered_at = datetime.now(timezone.utc)

    await db.flush()
    await db.refresh(delivery)
    return delivery