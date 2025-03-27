import logging
from typing import Annotated, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field

from core import settings
from app.core.utils import CoreUtils
from core.db_logging import AsyncDBLogger

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/logging")

class LogLevelUpdate(BaseModel):
    level: str

class LogEntry(BaseModel):
    timestamp: str
    level: str
    logger_name: str
    message: str
    exc_info: Optional[str] = None
    thread_name: Optional[str] = None
    process_name: Optional[str] = None

def verify_bearer(
    http_auth: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(HTTPBearer(description="Please provide AUTH_SECRET api key.", auto_error=False)),
    ],
) -> None:
    if not settings.AUTH_SECRET:
        return
    auth_secret = settings.AUTH_SECRET.get_secret_value()
    if not http_auth or http_auth.credentials != auth_secret:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

@router.get("/level")
@CoreUtils.aexception_handling_decorator
async def get_log_level():
    """Get current log level."""
    return {"level": logging.getLogger().getEffectiveLevel()}

@router.put("/level")
@CoreUtils.aexception_handling_decorator
async def update_log_level(update: LogLevelUpdate):
    """Update log level."""
    try:
        level = update.level.upper()
        logging.getLogger().setLevel(level)
        logger.info(f"Log level updated to {level}")
        return {"message": f"Log level updated to {level}"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid log level: {str(e)}")

@router.get("/entries", response_model=List[LogEntry])
@CoreUtils.aexception_handling_decorator
async def get_logs(
    level: Optional[str] = Query(None, description="Filter by log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)"),
    start_time: Optional[str] = Query(None, description="Filter logs after this ISO timestamp (e.g., 2023-01-01T00:00:00)"),
    end_time: Optional[str] = Query(None, description="Filter logs before this ISO timestamp (e.g., 2023-01-01T23:59:59)"),
    logger_name: Optional[str] = Query(None, description="Filter by logger name"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of log entries to return")
):
    """Query logs from the database with optional filters."""
    db_logger = AsyncDBLogger(db_path=settings.LOG_DB_PATH)
    
    logs = await db_logger.get_logs(level, start_time, end_time, logger_name, limit)
    
    return [LogEntry(**vars(log)) for log in logs]

@router.delete("/cleanup")
@CoreUtils.aexception_handling_decorator
async def cleanup_logs(days: int = Query(30, ge=1, description="Delete logs older than this many days")):
    """Delete old logs from the database."""
    db_logger = AsyncDBLogger(db_path=settings.LOG_DB_PATH)
    
    deleted_count = await db_logger.clear_old_logs(days)
    
    logger.info(f"Deleted {deleted_count} log entries older than {days} days")
    return {"message": f"Deleted {deleted_count} log entries older than {days} days"} 