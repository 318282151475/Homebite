import enum
from sqlalchemy import Column, Integer, String, Float, DateTime, Enum
from sqlalchemy.sql import func
from app.database import Base


class DeliveryStatus(str, enum.Enum):
    PENDING = "pending"                    # created, waiting for delivery person
    ACCEPTED = "accepted"                  # delivery person accepted
    PICKED_UP = "picked_up"               # picked up from chef
    OUT_FOR_DELIVERY = "out_for_delivery"  # on the way
    DELIVERED = "delivered"               # completed
    FAILED = "failed"                     # failed


class Delivery(Base):
    __tablename__ = "deliveries"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, unique=True, index=True, nullable=False)
    chef_id = Column(Integer, index=True, nullable=False)
    user_id = Column(Integer, index=True, nullable=False)
    delivery_person_id = Column(Integer, index=True, nullable=True)  # null until accepted
    delivery_person_name = Column(String(100), nullable=True)
    delivery_person_phone = Column(String(15), nullable=True)
    delivery_address = Column(String(500), nullable=False)
    city = Column(String(100), nullable=False)
    pincode = Column(String(10), nullable=False)
    status = Column(Enum(DeliveryStatus), default=DeliveryStatus.PENDING, nullable=False)
    estimated_delivery_minutes = Column(Integer, default=45, nullable=False)
    accepted_at = Column(DateTime(timezone=True), nullable=True)
    picked_up_at = Column(DateTime(timezone=True), nullable=True)
    delivered_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)