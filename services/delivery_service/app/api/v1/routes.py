from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.database import get_db
from ...schemas.delivery import DeliveryStatusUpdateRequest, DeliveryResponse
from ...crud.delivery import get_delivery_by_id, get_delivery_by_order_id, get_deliveries_by_user, \
    update_delivery_status
from ...core.exceptions import (
    DeliveryNotFoundException,
    InvalidDeliveryStatusTransitionException,
)
from app.kafka.producer import publish_event
from delivery_service.app.models.delivery import DeliveryStatus
from app.config import get_settings

settings = get_settings()
router = APIRouter(prefix="/api/v1/deliveries", tags=["deliveries"])

# Valid status transitions — you cannot go backwards
# PENDING → PICKED_UP → OUT_FOR_DELIVERY → DELIVERED
VALID_TRANSITIONS = {
    DeliveryStatus.PENDING: [DeliveryStatus.PICKED_UP, DeliveryStatus.FAILED],
    DeliveryStatus.PICKED_UP: [DeliveryStatus.OUT_FOR_DELIVERY, DeliveryStatus.FAILED],
    DeliveryStatus.OUT_FOR_DELIVERY: [DeliveryStatus.DELIVERED, DeliveryStatus.FAILED],
    DeliveryStatus.DELIVERED: [],   # terminal state
    DeliveryStatus.FAILED: [],      # terminal state
}


@router.get("/{delivery_id}", response_model=DeliveryResponse)
async def get_delivery(delivery_id: int, db: AsyncSession = Depends(get_db)):
    delivery = await get_delivery_by_id(db, delivery_id)
    if not delivery:
        raise DeliveryNotFoundException()
    return delivery


@router.get("/order/{order_id}", response_model=DeliveryResponse)
async def get_delivery_by_order(order_id: int, db: AsyncSession = Depends(get_db)):
    delivery = await get_delivery_by_order_id(db, order_id)
    if not delivery:
        raise DeliveryNotFoundException()
    return delivery


@router.get("/user/{user_id}", response_model=List[DeliveryResponse])
async def get_user_deliveries(user_id: int, db: AsyncSession = Depends(get_db)):
    return await get_deliveries_by_user(db, user_id)


@router.patch("/{delivery_id}/status", response_model=DeliveryResponse)
async def update_status(
    delivery_id: int,
    data: DeliveryStatusUpdateRequest,
    db: AsyncSession = Depends(get_db),
):
    delivery = await get_delivery_by_id(db, delivery_id)
    if not delivery:
        raise DeliveryNotFoundException()

    # enforce valid transitions — cannot skip states or go backwards
    if data.status not in VALID_TRANSITIONS[delivery.status]:
        raise InvalidDeliveryStatusTransitionException(
            current=delivery.status.value,
            requested=data.status.value,
        )

    updated = await update_delivery_status(
        db,
        delivery_id,
        data.status,
        data.delivery_person_name,
        data.delivery_person_phone,
    )

    # publish delivery.completed when delivered
    # chef_service consumes this to release chef back to available
    # order_service consumes this to mark order as delivered
    if data.status == DeliveryStatus.DELIVERED:
        await publish_event(
            topic=settings.KAFKA_TOPIC_DELIVERY_COMPLETED,
            event={
                "event": "delivery.completed",
                "delivery_id": delivery_id,
                "order_id": delivery.order_id,
                "chef_id": delivery.chef_id,
                "user_id": delivery.user_id,
            }
        )

    return updated