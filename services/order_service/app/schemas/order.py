from pydantic import BaseModel, field_validator
from typing import Optional, List
from datetime import datetime
from ..models.order import OrderStatus


class OrderItem(BaseModel):
    name: str
    qty: int
    price: float

    @field_validator("qty")
    @classmethod
    def qty_must_be_positive(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("Quantity must be at least 1")
        return v

    @field_validator("price")
    @classmethod
    def price_must_be_positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Price must be greater than 0")
        return v


class OrderCreateRequest(BaseModel):
    user_id: int
    chef_id: int
    items: List[OrderItem]
    delivery_address: str
    city: str
    pincode: str
    special_instructions: Optional[str] = None

    @field_validator("items")
    @classmethod
    def items_must_not_be_empty(cls, v: List[OrderItem]) -> List[OrderItem]:
        if not v:
            raise ValueError("Order must have at least one item")
        return v

    @field_validator("pincode")
    @classmethod
    def pincode_format(cls, v: str) -> str:
        if not v.isdigit() or len(v) != 6:
            raise ValueError("Pincode must be 6 digits")
        return v


class OrderResponse(BaseModel):
    id: int
    user_id: int
    chef_id: Optional[int]
    status: OrderStatus
    items: list
    total_amount: float
    delivery_address: str
    city: str
    pincode: str
    special_instructions: Optional[str]
    created_at: datetime
    updated_at: datetime
    delivered_at: Optional[datetime]

    model_config = {"from_attributes": True}


class OrderStatusUpdateRequest(BaseModel):
    status: OrderStatus