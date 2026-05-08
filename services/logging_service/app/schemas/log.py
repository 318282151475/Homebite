from pydantic import BaseModel
from typing import Optional, Any
from datetime import datetime
from ..models.log import LogLevel


class EventLogResponse(BaseModel):
    id: int
    service: str
    event_type: str
    level: LogLevel
    payload: Any
    message: Optional[str]
    order_id: Optional[int]
    user_id: Optional[int]
    chef_id: Optional[int]
    created_at: datetime

    model_config = {"from_attributes": True}


class LogQueryParams(BaseModel):
    service: Optional[str] = None
    event_type: Optional[str] = None
    level: Optional[LogLevel] = None
    order_id: Optional[int] = None
    user_id: Optional[int] = None
    limit: int = 50
    offset: int = 0