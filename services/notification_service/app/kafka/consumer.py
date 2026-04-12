import json
import logging
from aiokafka import AIOKafkaConsumer
from app.config import get_settings
from ..notifications.email import send_email
from ..notifications.templates import welcome_email, order_placed_email, chef_assigned_email, delivery_started_email, \
    delivery_completed_email, chef_assignment_failed_email

settings = get_settings()
logger = logging.getLogger(__name__)

_consumer: AIOKafkaConsumer | None = None


async def start_consumer() -> None:
    global _consumer
    _consumer = AIOKafkaConsumer(
        # notification_service subscribes to ALL topics
        # It reacts to every event in the system
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
    logger.info("Notification consumer started. Listening to all topics.")


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

            await route_event(event_type, event)

            # commit after successful processing
            await _consumer.commit()

        except Exception as e:
            logger.error(f"Error processing notification event: {e}", exc_info=True)
            # no commit — Kafka redelivers on next startup


async def route_event(event_type: str, event: dict) -> None:
    """
    Routes each event type to the correct notification handler.
    Adding a new notification = add one handler here. Nothing else changes.
    This is the Open/Closed principle — open for extension, closed for modification.
    """
    handlers = {
        "user.registered": handle_user_registered,
        "order.created": handle_order_created,
        "chef.assigned": handle_chef_assigned,
        "chef.assignment_failed": handle_chef_assignment_failed,
        "delivery.started": handle_delivery_started,
        "delivery.completed": handle_delivery_completed,
    }

    handler = handlers.get(event_type)
    if handler:
        await handler(event)
    else:
        logger.warning(f"No notification handler for event type: {event_type}")


async def handle_user_registered(event: dict) -> None:
    email = event.get("email")
    full_name = event.get("full_name", "there")
    if not email:
        logger.warning("user.registered event missing email field")
        return
    template = welcome_email(full_name)
    send_email(email, template["subject"], template["body"])


async def handle_order_created(event: dict) -> None:
    # In a real system, user email would come from user_service
    # Two options:
    # 1. Include email in the Kafka event payload (denormalization — preferred in microservices)
    # 2. Call user_service HTTP endpoint to fetch email (creates coupling)
    # We use option 1 — order_service should include user_email in event
    email = event.get("user_email")
    if not email:
        logger.warning("order.created event missing user_email field. Cannot send notification.")
        return
    order_id = event.get("order_id")
    total_amount = event.get("total_amount")
    template = order_placed_email(order_id, total_amount)
    send_email(email, template["subject"], template["body"])


async def handle_chef_assigned(event: dict) -> None:
    email = event.get("user_email")
    if not email:
        logger.warning("chef.assigned event missing user_email field")
        return
    order_id = event.get("order_id")
    chef_name = event.get("chef_name")
    template = chef_assigned_email(order_id, chef_name)
    send_email(email, template["subject"], template["body"])


async def handle_chef_assignment_failed(event: dict) -> None:
    email = event.get("user_email")
    if not email:
        return
    order_id = event.get("order_id")
    template = chef_assignment_failed_email(order_id)
    send_email(email, template["subject"], template["body"])


async def handle_delivery_started(event: dict) -> None:
    email = event.get("user_email")
    if not email:
        return
    order_id = event.get("order_id")
    template = delivery_started_email(order_id)
    send_email(email, template["subject"], template["body"])


async def handle_delivery_completed(event: dict) -> None:
    email = event.get("user_email")
    if not email:
        return
    order_id = event.get("order_id")
    template = delivery_completed_email(order_id)
    send_email(email, template["subject"], template["body"])