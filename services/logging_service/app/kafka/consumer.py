import json
import logging
from aiokafka import AIOKafkaConsumer
from app.config import get_settings
from app.database import AsyncSessionLocal
from ..crud.log import create_log
from ..models.log import LogLevel

settings = get_settings()
logger = logging.getLogger(__name__)

_consumer: AIOKafkaConsumer | None = None

# Maps event type to which service published it
# Used to tag logs with source service
EVENT_SOURCE_MAP = {
    "user.registered": "user_service",
    "order.created": "order_service",
    "chef.assigned": "chef_service",
    "chef.assignment_failed": "chef_service",
    "delivery.started": "delivery_service",
    "delivery.completed": "delivery_service",
}

# Events that represent failures — stored with WARNING level
FAILURE_EVENTS = {
    "chef.assignment_failed",
}


async def start_consumer() -> None:
    global _consumer
    _consumer = AIOKafkaConsumer(
        # logging_service subscribes to ALL topics — passive observer
        # It never publishes events — only reads and stores
        settings.KAFKA_TOPIC_USER_REGISTERED,
        settings.KAFKA_TOPIC_ORDER_CREATED,
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
    logger.info("Logging consumer started. Listening to all topics.")


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
            event_type = event.get("event", "unknown")
            logger.info(f"Logging event: {event_type}")

            await persist_event_log(event_type, event)
            await _consumer.commit()

        except Exception as e:
            logger.error(f"Failed to log event: {e}", exc_info=True)
            # logging failure should not block other services
            # commit anyway so we don't get stuck on one bad event
            # logging is observability — not critical path
            try:
                await _consumer.commit()
            except Exception:
                pass


async def persist_event_log(event_type: str, event: dict) -> None:
    """
    Persists every Kafka event to the logging DB.
    Extracts known reference IDs for indexed querying.
    """
    service = EVENT_SOURCE_MAP.get(event_type, "unknown")
    level = LogLevel.WARNING if event_type in FAILURE_EVENTS else LogLevel.INFO

    # extract reference IDs if present in event payload
    order_id = event.get("order_id")
    user_id = event.get("user_id")
    chef_id = event.get("chef_id")

    async with AsyncSessionLocal() as db:
        try:
            await create_log(
                db=db,
                service=service,
                event_type=event_type,
                payload=event,
                level=level,
                message=f"Event received: {event_type}",
                order_id=order_id,
                user_id=user_id,
                chef_id=chef_id,
            )
            await db.commit()
        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to persist log for event {event_type}: {e}", exc_info=True)
            raise