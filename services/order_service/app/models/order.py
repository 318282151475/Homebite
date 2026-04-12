from sqlalchemy import Column, Integer, String, Float, DateTime, Enum, JSON, ForeignKey
from sqlalchemy.sql import func
import enum
from app.database import Base


class OrderStatus(str, enum.Enum):
    PENDING = "pending"               # Order placed, waiting for chef
    CHEF_ASSIGNED = "chef_assigned"   # Chef accepted
    PREPARING = "preparing"           # Chef is cooking
    READY_FOR_PICKUP = "ready_for_pickup"
    OUT_FOR_DELIVERY = "out_for_delivery"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    FAILED = "failed"                 # No chef available


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)

    # user_id and chef_id reference other services
    # No FK constraints — microservices own their own DB
    user_id = Column(Integer, index=True, nullable=False)
    chef_id = Column(Integer, index=True, nullable=True)  # null until chef is assigned

    status = Column(Enum(OrderStatus), default=OrderStatus.PENDING, nullable=False)

    # items stored as JSON — flexible, no need for separate order_items table
    # Example: [{"name": "Dal Makhani", "qty": 2, "price": 180.0}]
    items = Column(JSON, nullable=False)

    total_amount = Column(Float, nullable=False)
    delivery_address = Column(String(500), nullable=False)
    city = Column(String(100), nullable=False)
    pincode = Column(String(10), nullable=False)
    special_instructions = Column(String(500), nullable=True)

    # Timestamps for each status transition — useful for SLA tracking
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    delivered_at = Column(DateTime(timezone=True), nullable=True)

    def __repr__(self) -> str:
        return f"<Order id={self.id} status={self.status} user_id={self.user_id}>"