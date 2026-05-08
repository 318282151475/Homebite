from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, List
from ..models.log import EventLog, LogLevel


async def create_log(
    db: AsyncSession,
    service: str,
    event_type: str,
    payload: dict,
    level: LogLevel = LogLevel.INFO,
    message: Optional[str] = None,
    order_id: Optional[int] = None,
    user_id: Optional[int] = None,
    chef_id: Optional[int] = None,
) -> EventLog:
    log = EventLog(
        service=service,
        event_type=event_type,
        level=level,
        payload=payload,
        message=message,
        order_id=order_id,
        user_id=user_id,
        chef_id=chef_id,
    )
    db.add(log)
    await db.flush()
    await db.refresh(log)
    return log


async def get_logs(
    db: AsyncSession,
    service: Optional[str] = None,
    event_type: Optional[str] = None,
    level: Optional[LogLevel] = None,
    order_id: Optional[int] = None,
    user_id: Optional[int] = None,
    limit: int = 50,
    offset: int = 0,
) -> List[EventLog]:
    query = select(EventLog).order_by(EventLog.created_at.desc())

    # apply filters only if provided
    if service:
        query = query.where(EventLog.service == service)
    if event_type:
        query = query.where(EventLog.event_type == event_type)
    if level:
        query = query.where(EventLog.level == level)
    if order_id:
        query = query.where(EventLog.order_id == order_id)
    if user_id:
        query = query.where(EventLog.user_id == user_id)

    query = query.limit(limit).offset(offset)
    result = await db.execute(query)
    return result.scalars().all()


async def get_log_by_id(db: AsyncSession, log_id: int) -> Optional[EventLog]:
    result = await db.execute(select(EventLog).where(EventLog.id == log_id))
    return result.scalar_one_or_none()