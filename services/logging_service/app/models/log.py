from sqlalchemy import Column, Integer, String, DateTime, Enum, JSON, Text
from sqlalchemy.sql import func
import enum
from app.database import Base


class LogLevel(str, enum.Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class EventLog(Base):
    __tablename__ = "event_logs"

    id = Column(Integer, primary_key=True, index=True)

    # which service published this event
    service = Column(String(100), nullable=False, index=True)

    # event type — e.g. "order.created", "chef.assigned"
    event_type = Column(String(100), nullable=False, index=True)

    # log level — INFO for normal events, ERROR for failures
    level = Column(Enum(LogLevel), default=LogLevel.INFO, nullable=False, index=True)

    # full event payload stored as JSON
    # allows querying any field in the event later
    payload = Column(JSON, nullable=False)

    # human readable message
    message = Column(Text, nullable=True)

    # optional reference IDs for fast lookup
    # e.g. find all logs for order_id=123
    order_id = Column(Integer, nullable=True, index=True)
    user_id = Column(Integer, nullable=True, index=True)
    chef_id = Column(Integer, nullable=True, index=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    def __repr__(self) -> str:
        return f"<EventLog id={self.id} event={self.event_type} service={self.service}>"