import json
import logging
from aiokafka import AIOKafkaConsumer
from app.config import get_settings
from app.database import AsyncSessionLocal
from ..crud.delivery import create_delivery, get_delivery_by_order_id
from ..models.delivery import DeliveryStatus
from ..schemas.delivery import DeliveryCreateRequest

settings = get_settings()
logger = logging.getLogger(__name__)

_consumer: AIOKafkaConsumer | None = None


async def start_consumer() -> None:
    global _consumer
    _consumer = AIOKafkaConsumer(
        settings.KAFKA_TOPIC_CHEF_ASSIGNED,
        bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
        group_id=settings.KAFKA_CONSUMER_GROUP,
        auto_offset_reset="earliest",
        value_deserializer=lambda v: json.loads(v.decode("utf-8")),
        enable_auto_commit=False,
    )
    await _consumer.start()
    logger.info(f"Kafka consumer started. Listening on: {settings.KAFKA_TOPIC_CHEF_ASSIGNED}")


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

            await _consumer.commit()

        except Exception as e:
            logger.error(f"Error processing event: {e}", exc_info=True)


async def handle_chef_assigned(event: dict) -> None:
    """
    When chef is assigned to an order:
    - Create delivery record with status=pending
    - Do NOT publish any event here
    - delivery.started is published when delivery person marks picked_up
    - delivery.completed is published when delivery person marks delivered
    """
    order_id = event.get("order_id")
    chef_id = event.get("chef_id")
    user_id = event.get("user_id")
    city = event.get("city")

    async with AsyncSessionLocal() as db:
        try:
            # idempotency check — prevent duplicate delivery records
            existing = await get_delivery_by_order_id(db, order_id)
            if existing:
                logger.warning(f"Delivery already exists for order {order_id}. Skipping.")
                return

            delivery = await create_delivery(
                db,
                DeliveryCreateRequest(
                    order_id=order_id,
                    chef_id=chef_id,
                    user_id=user_id,
                    delivery_address=event.get("delivery_address", ""),
                    city=city,
                    pincode=event.get("pincode", "000000"),
                )
            )
            await db.commit()
            logger.info(f"Delivery {delivery.id} created for order {order_id}. Waiting for delivery person to accept.")

        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to create delivery for order {order_id}: {e}", exc_info=True)
            raise