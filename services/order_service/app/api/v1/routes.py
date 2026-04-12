from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.database import get_db
from ...schemas.order import OrderCreateRequest, OrderResponse, OrderStatusUpdateRequest
from ...crud.order import create_order, get_order_by_id, get_orders_by_user, cancel_order
from ...core.exceptions import OrderNotFoundException, OrderCancellationNotAllowedException
from app.kafka.producer import publish_event
from app.config import get_settings

#Metrics starts

from ...metrics import orders_placed_total, orders_in_progress, kafka_events_published_total

#Metrics ends


settings = get_settings()
router = APIRouter(prefix="/api/v1/orders", tags=["orders"])

#Metrics starts

@router.post("/", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def place_order(data: OrderCreateRequest, db: AsyncSession = Depends(get_db)):
    orders_in_progress.inc()   # increment gauge — one more order being processed
    try:
        order = await create_order(db, data)

        await publish_event(
            topic=settings.KAFKA_TOPIC_ORDER_CREATED,
            event={
                "event": "order.created",
                "order_id": order.id,
                "user_id": order.user_id,
                "city": order.city,
                "pincode": order.pincode,
                "total_amount": order.total_amount,
                "items": order.items,
            }
        )

        orders_placed_total.inc()                                    # increment counter
        kafka_events_published_total.labels(
            topic=settings.KAFKA_TOPIC_ORDER_CREATED
        ).inc()

        return order
    finally:
        orders_in_progress.dec()   # always decrement gauge when done

#Metrics ends




@router.post("/", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def place_order(data: OrderCreateRequest, db: AsyncSession = Depends(get_db)):
    order = await create_order(db, data)

    # Publish order.created — chef_service and notification_service will consume this
    # order_service does NOT call chef_service directly
    # This is the core of async microservices — loose coupling
    await publish_event(
        topic=settings.KAFKA_TOPIC_ORDER_CREATED,
        event={
            "event": "order.created",
            "order_id": order.id,
            "user_id": order.user_id,
            "city": order.city,
            "pincode": order.pincode,
            "total_amount": order.total_amount,
            "items": order.items,
        }
    )

    return order


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(order_id: int, db: AsyncSession = Depends(get_db)):
    order = await get_order_by_id(db, order_id)
    if not order:
        raise OrderNotFoundException()
    return order


@router.get("/user/{user_id}", response_model=List[OrderResponse])
async def get_user_orders(user_id: int, db: AsyncSession = Depends(get_db)):
    return await get_orders_by_user(db, user_id)


@router.post("/{order_id}/cancel", response_model=OrderResponse)
async def cancel_user_order(order_id: int, db: AsyncSession = Depends(get_db)):
    order = await cancel_order(db, order_id)
    if not order:
        raise OrderCancellationNotAllowedException()
    return order