from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, List
from ..models.order import Order, OrderStatus
from ..schemas.order import OrderCreateRequest


def calculate_total(items: list) -> float:
    return round(sum(item.price * item.qty for item in items), 2)


async def create_order(db: AsyncSession, data: OrderCreateRequest) -> Order:
    order = Order(
        user_id=data.user_id,
        items=[item.model_dump() for item in data.items],
        total_amount=calculate_total(data.items),
        delivery_address=data.delivery_address,
        city=data.city,
        pincode=data.pincode,
        special_instructions=data.special_instructions,
        status=OrderStatus.PENDING,
    )
    db.add(order)
    await db.flush()
    await db.refresh(order)
    return order


async def get_order_by_id(db: AsyncSession, order_id: int) -> Optional[Order]:
    result = await db.execute(select(Order).where(Order.id == order_id))
    return result.scalar_one_or_none()


async def get_orders_by_user(db: AsyncSession, user_id: int) -> List[Order]:
    result = await db.execute(
        select(Order)
        .where(Order.user_id == user_id)
        .order_by(Order.created_at.desc())
    )
    return result.scalars().all()


async def update_order_status(
    db: AsyncSession,
    order_id: int,
    status: OrderStatus,
    chef_id: Optional[int] = None,
) -> Optional[Order]:
    order = await get_order_by_id(db, order_id)
    if not order:
        return None
    order.status = status
    if chef_id:
        order.chef_id = chef_id
    if status == OrderStatus.DELIVERED:
        from datetime import datetime, timezone
        order.delivered_at = datetime.now(timezone.utc)
    await db.flush()
    await db.refresh(order)
    return order


async def cancel_order(db: AsyncSession, order_id: int) -> Optional[Order]:
    order = await get_order_by_id(db, order_id)
    if not order:
        return None
    # Only cancellable in early stages
    if order.status not in [OrderStatus.PENDING, OrderStatus.CHEF_ASSIGNED]:
        return None
    order.status = OrderStatus.CANCELLED
    await db.flush()
    await db.refresh(order)
    return order