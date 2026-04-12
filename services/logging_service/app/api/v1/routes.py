from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List

from app.database import get_db
from ...schemas.log import EventLogResponse
from ...crud.log import get_logs, get_log_by_id
from ...models.log import LogLevel
from ...core.exceptions import LogNotFoundException

router = APIRouter(prefix="/api/v1/logs", tags=["logs"])


@router.get("/", response_model=List[EventLogResponse])
async def query_logs(
    service: Optional[str] = Query(None),
    event_type: Optional[str] = Query(None),
    level: Optional[LogLevel] = Query(None),
    order_id: Optional[int] = Query(None),
    user_id: Optional[int] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """
    Query logs with filters.
    Examples:
    GET /api/v1/logs?order_id=123        → all events for order 123
    GET /api/v1/logs?service=order_service → all events from order_service
    GET /api/v1/logs?level=warning        → all warning level events
    GET /api/v1/logs?user_id=45           → all events involving user 45
    """
    return await get_logs(
        db=db,
        service=service,
        event_type=event_type,
        level=level,
        order_id=order_id,
        user_id=user_id,
        limit=limit,
        offset=offset,
    )


@router.get("/{log_id}", response_model=EventLogResponse)
async def get_log(log_id: int, db: AsyncSession = Depends(get_db)):
    log = await get_log_by_id(db, log_id)
    if not log:
        raise LogNotFoundException()
    return log