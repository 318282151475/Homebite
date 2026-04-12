from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    APP_ENV: str = "development"
    APP_NAME: str = "delivery_service"
    APP_PORT: int = 8004
    DEBUG: bool = False

    DB_HOST: str
    DB_PORT: int = 3306
    DB_NAME: str
    DB_USER: str
    DB_PASSWORD: str

    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9092"
    KAFKA_TOPIC_CHEF_ASSIGNED: str = "chef.assigned"
    KAFKA_TOPIC_DELIVERY_STARTED: str = "delivery.started"
    KAFKA_TOPIC_DELIVERY_COMPLETED: str = "delivery.completed"
    KAFKA_CONSUMER_GROUP: str = "delivery-service-group"

    @property
    def DATABASE_URL(self) -> str:
        return (
            f"mysql+aiomysql://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()