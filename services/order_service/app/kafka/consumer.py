#This is the most critical file — order_service listens to chef.assigned and delivery_service.completed to update order status automatically.

import json
import logging
from aiokafka import AIOKafkaConsumer
from app.config import get_settings
from app.database import AsyncSessionLocal
from ..crud.order import update_order_status
from ..models.order import OrderStatus

settings = get_settings()
logger = logging.getLogger(__name__)

_consumer: AIOKafkaConsumer | None = None


async def start_consumer() -> None:
    global _consumer
    _consumer = AIOKafkaConsumer(
        # Subscribing to multiple topics in one consumer
        settings.KAFKA_TOPIC_CHEF_ASSIGNED,
        settings.KAFKA_TOPIC_DELIVERY_STARTED,
        settings.KAFKA_TOPIC_DELIVERY_COMPLETED,
        bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
        group_id=settings.KAFKA_CONSUMER_GROUP,
        auto_offset_reset="earliest",
        value_deserializer=lambda v: json.loads(v.decode("utf-8")),
        enable_auto_commit=False,
    )
    await _consumer.start()
    logger.info("Kafka consumer started")


async def stop_consumer() -> None:
    global _consumer
    if _consumer:
        await _consumer.stop()


async def consume_events() -> None:
    if not _consumer:
        return

    async for message in _consumer:
        try:
            event = message.value
            event_type = event.get("event")
            logger.info(f"Received event: {event_type}")

            if event_type == "chef.assigned":
                await handle_chef_assigned(event)

            elif event_type == "chef.assignment_failed":
                await handle_chef_assignment_failed(event)

            elif event_type == "delivery_service.started":
                await handle_delivery_started(event)

            elif event_type == "delivery_service.completed":
                await handle_delivery_completed(event)

            await _consumer.commit()

        except Exception as e:
            logger.error(f"Error processing event: {e}", exc_info=True)


async def handle_chef_assigned(event: dict) -> None:
    order_id = event.get("order_id")
    chef_id = event.get("chef_id")
    async with AsyncSessionLocal() as db:
        try:
            await update_order_status(db, order_id, OrderStatus.CHEF_ASSIGNED, chef_id=chef_id)
            await db.commit()
            logger.info(f"Order {order_id} updated to CHEF_ASSIGNED with chef {chef_id}")
        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to update order {order_id}: {e}", exc_info=True)
            raise


async def handle_chef_assignment_failed(event: dict) -> None:
    order_id = event.get("order_id")
    async with AsyncSessionLocal() as db:
        try:
            await update_order_status(db, order_id, OrderStatus.FAILED)
            await db.commit()
            logger.info(f"Order {order_id} marked as FAILED — no chef available")
        except Exception as e:
            await db.rollback()
            raise


async def handle_delivery_started(event: dict) -> None:
    order_id = event.get("order_id")
    async with AsyncSessionLocal() as db:
        try:
            await update_order_status(db, order_id, OrderStatus.OUT_FOR_DELIVERY)
            await db.commit()
        except Exception as e:
            await db.rollback()
            raise


async def handle_delivery_completed(event: dict) -> None:
    order_id = event.get("order_id")
    async with AsyncSessionLocal() as db:
        try:
            await update_order_status(db, order_id, OrderStatus.DELIVERED)
            await db.commit()
            logger.info(f"Order {order_id} delivered successfully")
        except Exception as e:
            await db.rollback()
            raise