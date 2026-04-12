from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    APP_ENV: str = "development"
    APP_NAME: str = "notification_service"
    APP_PORT: int = 8005
    DEBUG: bool = False

    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9092"
    KAFKA_TOPIC_USER_REGISTERED: str = "user.registered"
    KAFKA_TOPIC_ORDER_CREATED: str = "order.created"
    KAFKA_TOPIC_CHEF_ASSIGNED: str = "chef.assigned"
    KAFKA_TOPIC_DELIVERY_STARTED: str = "delivery.started"
    KAFKA_TOPIC_DELIVERY_COMPLETED: str = "delivery.completed"
    KAFKA_CONSUMER_GROUP: str = "notification-service-group"

    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    EMAIL_FROM: str = "noreply@homebite.com"

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()