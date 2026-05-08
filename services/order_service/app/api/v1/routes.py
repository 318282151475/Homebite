from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.database import get_db
from ...schemas.order import OrderCreateRequest, OrderResponse, OrderStatusUpdateRequest
from ...crud.order import create_order, get_order_by_id, get_orders_by_user, get_orders_by_chef, update_order_status, \
    cancel_order
from ...core.exceptions import OrderNotFoundException, OrderCancellationNotAllowedException, \
    InvalidOrderStatusTransitionException
from app.kafka.producer import publish_event
from app.config import get_settings
from ...models.order import OrderStatus
from ...metrics import orders_placed_total, orders_in_progress, kafka_events_published_total, orders_cancelled_total


settings = get_settings()
router = APIRouter(prefix="/api/v1/orders", tags=["orders"])

# Valid transitions chef is allowed to make
CHEF_VALID_TRANSITIONS = {
    OrderStatus.CHEF_ASSIGNED: OrderStatus.PREPARING,
    OrderStatus.PREPARING: OrderStatus.READY_FOR_PICKUP,
}


@router.post("/", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def place_order(data: OrderCreateRequest, db: AsyncSession = Depends(get_db)):
    orders_in_progress.inc()
    try:
        order = await create_order(db, data)

        await publish_event(
            topic=settings.KAFKA_TOPIC_ORDER_CREATED,
            event={
                "event": "order.created",
                "order_id": order.id,
                "user_id": order.user_id,
                "chef_id": order.chef_id,
                "city": order.city,
                "pincode": order.pincode,
                "delivery_address": order.delivery_address,
                "total_amount": order.total_amount,
                "items": order.items,
            }
        )

        orders_placed_total.inc()
        kafka_events_published_total.labels(
            topic=settings.KAFKA_TOPIC_ORDER_CREATED
        ).inc()

        return order
    finally:
        orders_in_progress.dec()


@router.get("/chef/{chef_id}", response_model=List[OrderResponse])
async def get_chef_orders(chef_id: int, db: AsyncSession = Depends(get_db)):
    """Chef sees only orders assigned to them."""
    return await get_orders_by_chef(db, chef_id)


@router.get("/user/{user_id}", response_model=List[OrderResponse])
async def get_user_orders(user_id: int, db: AsyncSession = Depends(get_db)):
    return await get_orders_by_user(db, user_id)


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(order_id: int, db: AsyncSession = Depends(get_db)):
    order = await get_order_by_id(db, order_id)
    if not order:
        raise OrderNotFoundException()
    return order


@router.patch("/{order_id}/status", response_model=OrderResponse)
async def update_status(
    order_id: int,
    data: OrderStatusUpdateRequest,
    db: AsyncSession = Depends(get_db),
):
    """Chef updates order status: chef_assigned → preparing → ready_for_pickup."""
    order = await get_order_by_id(db, order_id)
    if not order:
        raise OrderNotFoundException()

    # validate transition
    allowed_next = CHEF_VALID_TRANSITIONS.get(order.status)
    if allowed_next != data.status:
        raise InvalidOrderStatusTransitionException(
            current=order.status.value,
            requested=data.status.value,
        )

    updated = await update_order_status(db, order_id, data.status)
    return updated


@router.post("/{order_id}/cancel", response_model=OrderResponse)
async def cancel_user_order(order_id: int, db: AsyncSession = Depends(get_db)):
    order = await cancel_order(db, order_id)
    if not order:
        raise OrderCancellationNotAllowedException()
    orders_cancelled_total.inc()
    return order