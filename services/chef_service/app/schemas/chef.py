from pydantic import BaseModel, field_validator
from typing import Optional
from datetime import datetime
from chef_service.app.models.chef import ChefStatus, CuisineType


class ChefCreateRequest(BaseModel):
    user_id: int
    full_name: str
    bio: Optional[str] = None
    cuisine_type: CuisineType
    experience_years: int = 0
    city: str
    pincode: str

    @field_validator("experience_years")
    @classmethod
    def experience_must_be_positive(cls, v: int) -> int:
        if v < 0:
            raise ValueError("Experience years cannot be negative")
        return v

    @field_validator("pincode")
    @classmethod
    def pincode_format(cls, v: str) -> str:
        if not v.isdigit() or len(v) != 6:
            raise ValueError("Pincode must be 6 digits")
        return v


class ChefStatusUpdateRequest(BaseModel):
    status: ChefStatus


class ChefResponse(BaseModel):
    id: int
    user_id: int
    full_name: str
    bio: Optional[str]
    cuisine_type: CuisineType
    experience_years: int
    rating: float
    total_orders: int
    status: ChefStatus
    is_active: bool
    city: str
    pincode: str
    created_at: datetime

    model_config = {"from_attributes": True}


# Used internally by order_service via Kafka response
class ChefAssignmentResponse(BaseModel):
    chef_id: int
    chef_name: str
    order_id: int
    status: str = "assigned"