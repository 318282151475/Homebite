from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from ..models.delivery import DeliveryStatus


class DeliveryCreateRequest(BaseModel):
    order_id: int
    chef_id: int
    user_id: int
    delivery_address: str
    city: str
    pincode: str
    estimated_delivery_minutes: int = 45


class DeliveryStatusUpdateRequest(BaseModel):
    status: DeliveryStatus
    delivery_person_name: Optional[str] = None
    delivery_person_phone: Optional[str] = None


class DeliveryAcceptRequest(BaseModel):
    delivery_person_id: int
    delivery_person_name: str
    delivery_person_phone: Optional[str] = None


class DeliveryResponse(BaseModel):
    id: int
    order_id: int
    chef_id: int
    user_id: int
    delivery_person_id: Optional[int] = None
    delivery_person_name: Optional[str] = None
    delivery_person_phone: Optional[str] = None
    delivery_address: str
    city: str
    pincode: str
    status: DeliveryStatus
    estimated_delivery_minutes: int
    accepted_at: Optional[datetime] = None
    picked_up_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}