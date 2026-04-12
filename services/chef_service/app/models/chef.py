from sqlalchemy import Column, Integer, String, Boolean, Float, DateTime, Enum, Text
from sqlalchemy.sql import func
import enum
from app.database import Base


class ChefStatus(str, enum.Enum):
    AVAILABLE = "available"
    BUSY = "busy"
    OFFLINE = "offline"


class CuisineType(str, enum.Enum):
    NORTH_INDIAN = "north_indian"
    SOUTH_INDIAN = "south_indian"
    CHINESE = "chinese"
    CONTINENTAL = "continental"
    STREET_FOOD = "street_food"
    DESSERTS = "desserts"


class Chef(Base):
    __tablename__ = "chefs"

    id = Column(Integer, primary_key=True, index=True)

    # user_id links to user_service — but NO foreign key constraint
    # In microservices, cross-service DB constraints are forbidden
    # Each DB is owned by its service — chef_service cannot reference user_service DB
    # Consistency is maintained at application level, not DB level
    user_id = Column(Integer, unique=True, index=True, nullable=False)

    full_name = Column(String(100), nullable=False)
    bio = Column(Text, nullable=True)
    cuisine_type = Column(Enum(CuisineType), nullable=False)
    experience_years = Column(Integer, default=0)
    rating = Column(Float, default=0.0)
    total_orders = Column(Integer, default=0)
    status = Column(Enum(ChefStatus), default=ChefStatus.OFFLINE, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    city = Column(String(100), nullable=False)
    pincode = Column(String(10), nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self) -> str:
        return f"<Chef id={self.id} name={self.full_name} status={self.status}>"