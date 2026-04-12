from pydantic import BaseModel, field_validator
from typing import Optional
from datetime import datetime
from delivery_service.app.models.delivery import DeliveryStatus


class DeliveryCreateRequest(BaseModel):
    order_id: int
    chef_id: int
    user_id: int
    delivery_address: str
    city: str
    pincode: str

    @field_validator("pincode")
    @classmethod
    def pincode_format(cls, v: str) -> str:
        if not v.isdigit() or len(v) != 6:
            raise ValueError("Pincode must be 6 digits")
        return v


class DeliveryStatusUpdateRequest(BaseModel):
    status: DeliveryStatus
    delivery_person_name: Optional[str] = None
    delivery_person_phone: Optional[str] = None


class DeliveryResponse(BaseModel):
    id: int
    order_id: int
    chef_id: int
    user_id: int
    status: DeliveryStatus
    delivery_address: str
    city: str
    pincode: str
    delivery_person_name: Optional[str]
    delivery_person_phone: Optional[str]
    estimated_delivery_minutes: int
    created_at: datetime
    updated_at: datetime
    picked_up_at: Optional[datetime]
    delivered_at: Optional[datetime]

    model_config = {"from_attributes": True}