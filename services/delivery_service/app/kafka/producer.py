import json
import logging
from aiokafka import AIOKafkaProducer
from app.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

_producer: AIOKafkaProducer | None = None


async def start_producer() -> None:
    global _producer
    _producer = AIOKafkaProducer(
        bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        acks="all",
        retries=3,
    )
    await _producer.start()
    logger.info("Kafka producer started")


async def stop_producer() -> None:
    global _producer
    if _producer:
        await _producer.stop()


async def publish_event(topic: str, event: dict) -> None:
    if not _producer:
        logger.error("Kafka producer not initialized")
        return
    try:
        await _producer.send_and_wait(topic, value=event)
        logger.info(f"Event published to '{topic}': {event}")
    except Exception as e:
        logger.error(f"Failed to publish to '{topic}': {e}")