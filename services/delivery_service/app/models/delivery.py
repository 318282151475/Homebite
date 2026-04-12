from sqlalchemy import Column, Integer, String, DateTime, Enum, Float
from sqlalchemy.sql import func
import enum
from app.database import Base


class DeliveryStatus(str, enum.Enum):
    PENDING = "pending"                  # chef.assigned received, delivery record created
    PICKED_UP = "picked_up"              # delivery person picked up food from chef
    OUT_FOR_DELIVERY = "out_for_delivery" # on the way to customer
    DELIVERED = "delivered"              # successfully delivered
    FAILED = "failed"                    # delivery failed


class Delivery(Base):
    __tablename__ = "deliveries"

    id = Column(Integer, primary_key=True, index=True)

    # order_id and chef_id from other services — no FK constraint
    # microservices never share DB, consistency is at application level
    order_id = Column(Integer, unique=True, index=True, nullable=False)
    chef_id = Column(Integer, index=True, nullable=False)
    user_id = Column(Integer, index=True, nullable=False)

    status = Column(Enum(DeliveryStatus), default=DeliveryStatus.PENDING, nullable=False)

    delivery_address = Column(String(500), nullable=False)
    city = Column(String(100), nullable=False)
    pincode = Column(String(10), nullable=False)

    # delivery_person details — in real system this would be a separate service
    # keeping simple for HomeBite scope
    delivery_person_name = Column(String(100), nullable=True)
    delivery_person_phone = Column(String(15), nullable=True)

    # estimated and actual delivery times — useful for SLA tracking
    estimated_delivery_minutes = Column(Integer, default=45, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    picked_up_at = Column(DateTime(timezone=True), nullable=True)
    delivered_at = Column(DateTime(timezone=True), nullable=True)

    def __repr__(self) -> str:
        return f"<Delivery id={self.id} order_id={self.order_id} status={self.status}>"