#This is the most important file in chef_service. This is where async magic happens.

import json
import logging
from aiokafka import AIOKafkaConsumer
from app.config import get_settings
from app.database import AsyncSessionLocal
from app.crud.chef import get_available_chefs, assign_chef_to_order, get_chef_by_id
from app.models.chef import ChefStatus
from app.kafka.producer import publish_event
from app.metrics import chefs_assigned_total, chef_assignment_failed_total, kafka_events_consumed_total

settings = get_settings()
logger = logging.getLogger(__name__)

_consumer: AIOKafkaConsumer | None = None


async def start_consumer() -> None:
    global _consumer
    _consumer = AIOKafkaConsumer(
        settings.KAFKA_TOPIC_ORDER_CREATED,
        bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
        group_id=settings.KAFKA_CONSUMER_GROUP,
        auto_offset_reset="earliest",
        value_deserializer=lambda v: json.loads(v.decode("utf-8")),
        enable_auto_commit=False,
    )
    await _consumer.start()
    logger.info(f"Kafka consumer started. Listening on: {settings.KAFKA_TOPIC_ORDER_CREATED}")


async def stop_consumer() -> None:
    global _consumer
    if _consumer:
        await _consumer.stop()


async def consume_events() -> None:
    """
    Infinite loop that processes incoming Kafka events.
    Runs as a background task from app startup.
    """
    if not _consumer:
        logger.error("Consumer not initialized")
        return

    async for message in _consumer:
        try:
            event = message.value
            logger.info(f"Received event: {event}")

            if event.get("event") == "order.created":
                await handle_order_created(event)

            await _consumer.commit()

        except Exception as e:
            logger.error(f"Error processing event: {e}", exc_info=True)


async def handle_order_created(event: dict) -> None:
    """
    When order.created event arrives:
    1. Find an available chef in the same city
    2. Mark chef as BUSY
    3. Publish chef.assigned event
    If no chef is available, publish chef.assignment_failed event
    """

    order_id = event.get("order_id")
    city = event.get("city")
    user_id = event.get("user_id")
    requested_chef_id = event.get("chef_id")

    async with AsyncSessionLocal() as db:
        try:
            if requested_chef_id:
                # Customer chose a specific chef — use that chef
                assigned_chef = await get_chef_by_id(db, requested_chef_id)
                if not assigned_chef or assigned_chef.status != ChefStatus.AVAILABLE:
                    # Chef not available — fall back to auto-assign
                    available_chefs = await get_available_chefs(db, city)
                    if not available_chefs:
                        await publish_event(
                            topic=settings.KAFKA_TOPIC_CHEF_ASSIGNED,
                            event={
                                "event": "chef.assignment_failed",
                                "order_id": order_id,
                                "reason": "Requested chef not available",
                                "user_id": user_id,
                            }
                        )
                        chef_assignment_failed_total.inc()
                        return
                    assigned_chef = max(available_chefs, key=lambda c: c.rating)
            else:
                # No chef specified — auto-assign best available
                available_chefs = await get_available_chefs(db, city)
                if not available_chefs:
                    await publish_event(
                        topic=settings.KAFKA_TOPIC_CHEF_ASSIGNED,
                        event={
                            "event": "chef.assignment_failed",
                            "order_id": order_id,
                            "reason": "No available chefs",
                            "user_id": user_id,
                        }
                        )
                    chef_assignment_failed_total.inc()
                    return
                assigned_chef = max(available_chefs, key=lambda c: c.rating)

            # Mark chef as busy
            assigned_chef = await assign_chef_to_order(db, assigned_chef.id)
            await db.commit()

            # increment metrics after successful assignment
            chefs_assigned_total.inc()
            kafka_events_consumed_total.labels(
                topic="order.created",
                event_type="order.created"
            ).inc()

            await publish_event(
                topic=settings.KAFKA_TOPIC_CHEF_ASSIGNED,
                event={
                    "event": "chef.assigned",
                    "order_id": order_id,
                    "chef_id": assigned_chef.id,
                    "chef_name": assigned_chef.full_name,
                    "city": city,
                    "user_id": user_id,
                    "pincode": event.get("pincode", ""),
                    "delivery_address": event.get("delivery_address", ""),
                }
            )

        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to assign chef for order {order_id}: {e}", exc_info=True)
            raise