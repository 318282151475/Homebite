from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
import logging

from app.database import get_db
from ...schemas.delivery import DeliveryCreateRequest, DeliveryStatusUpdateRequest, DeliveryAcceptRequest, \
    DeliveryResponse
from ...crud.delivery import create_delivery, get_delivery_by_id, get_delivery_by_order_id, get_deliveries_by_user, \
    get_deliveries_by_delivery_person, get_available_deliveries, accept_delivery, update_delivery_status
from ...models.delivery import DeliveryStatus
from app.kafka.producer import publish_event
from app.config import get_settings
from ...metrics import deliveries_created_total, deliveries_completed_total, deliveries_failed_total, \
    delivery_duration_minutes

logger = logging.getLogger(__name__)
settings = get_settings()
router = APIRouter(prefix="/api/v1/deliveries", tags=["deliveries"])


@router.get("/available/{city}", response_model=List[DeliveryResponse])
async def list_available_deliveries(city: str, db: AsyncSession = Depends(get_db)):
    """
    Returns all unassigned deliveries in a city.
    Delivery persons browse this list and accept orders.
    """
    return await get_available_deliveries(db, city)


@router.get("/person/{delivery_person_id}", response_model=List[DeliveryResponse])
async def get_my_deliveries(
    delivery_person_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Delivery person sees all deliveries assigned to them."""
    return await get_deliveries_by_delivery_person(db, delivery_person_id)


@router.get("/user/{user_id}", response_model=List[DeliveryResponse])
async def get_user_deliveries(
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Customer sees delivery status for their orders."""
    return await get_deliveries_by_user(db, user_id)


@router.get("/order/{order_id}", response_model=DeliveryResponse)
async def get_delivery_by_order(
    order_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get delivery record by order ID."""
    delivery = await get_delivery_by_order_id(db, order_id)
    if not delivery:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Delivery not found for this order"
        )
    return delivery


@router.post("/{delivery_id}/accept", response_model=DeliveryResponse)
async def accept_delivery_request(
    delivery_id: int,
    data: DeliveryAcceptRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Delivery person accepts an available delivery.
    Sets delivery_person_id and changes status to accepted.
    If already accepted by someone else returns 409.
    """
    delivery = await accept_delivery(
        db,
        delivery_id=delivery_id,
        delivery_person_id=data.delivery_person_id,
        delivery_person_name=data.delivery_person_name,
        delivery_person_phone=data.delivery_person_phone,
    )
    if not delivery:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Delivery already accepted by someone else"
        )
    await db.commit()

    # increment counter when delivery person accepts
    deliveries_created_total.inc()

    return delivery


@router.patch("/{delivery_id}/status", response_model=DeliveryResponse)
async def update_status(
    delivery_id: int,
    data: DeliveryStatusUpdateRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Update delivery status.
    Flow: accepted → picked_up → out_for_delivery → delivered

    picked_up    → publishes delivery.started  → order_service updates to OUT_FOR_DELIVERY
    delivered    → publishes delivery.completed → order_service updates to DELIVERED
                                                → chef_service resets chef to AVAILABLE
    """
    delivery = await update_delivery_status(
        db,
        delivery_id=delivery_id,
        new_status=data.status,
        delivery_person_name=data.delivery_person_name,
        delivery_person_phone=data.delivery_person_phone,
    )
    if not delivery:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Delivery not found"
        )

    await db.commit()

    # publish delivery.started when delivery person picks up food
    # order_service consumes this → updates order status to OUT_FOR_DELIVERY
    if data.status == DeliveryStatus.PICKED_UP:
        await publish_event(
            topic=settings.KAFKA_TOPIC_DELIVERY_STARTED,
            event={
                "event": "delivery.started",
                "delivery_id": delivery.id,
                "order_id": delivery.order_id,
                "chef_id": delivery.chef_id,
                "user_id": delivery.user_id,
                "city": delivery.city,
            }
        )
        logger.info(f"Published delivery.started for order {delivery.order_id}")

    # publish delivery.completed when order is delivered
    # order_service consumes this → updates order status to DELIVERED
    # chef_service consumes this  → resets chef status to AVAILABLE
    if data.status == DeliveryStatus.DELIVERED:
        await publish_event(
            topic=settings.KAFKA_TOPIC_DELIVERY_COMPLETED,
            event={
                "event": "delivery.completed",
                "delivery_id": delivery.id,
                "order_id": delivery.order_id,
                "chef_id": delivery.chef_id,
                "user_id": delivery.user_id,
                "delivery_person_id": delivery.delivery_person_id,
            }
        )
        logger.info(f"Published delivery.completed for order {delivery.order_id}")

        # increment completed counter
        deliveries_completed_total.inc()

        # track delivery duration using histogram
        # calculated from created_at to now
        if delivery.created_at:
            from datetime import datetime, timezone
            now = datetime.now(timezone.utc)
            created = delivery.created_at.replace(tzinfo=timezone.utc) if delivery.created_at.tzinfo is None else delivery.created_at
            duration_minutes = (now - created).total_seconds() / 60
            delivery_duration_minutes.observe(duration_minutes)
            logger.info(f"Delivery {delivery.id} completed in {duration_minutes:.1f} minutes")

    return delivery


@router.get("/{delivery_id}", response_model=DeliveryResponse)
async def get_delivery(
    delivery_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get a single delivery by ID."""
    delivery = await get_delivery_by_id(db, delivery_id)
    if not delivery:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Delivery not found"
        )
    return delivery