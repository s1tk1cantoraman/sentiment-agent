import logging
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from core import settings
from service.utils import CoreUtils

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/logging")

class LogLevelUpdate(BaseModel):
    level: str

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
@CoreUtils.exception_handling_decorator
def get_log_level():
    """Get current log level."""
    return {"level": logging.getLogger().getEffectiveLevel()}

@router.put("/level")
@CoreUtils.exception_handling_decorator
def update_log_level(update: LogLevelUpdate):
    """Update log level."""
    try:
        level = update.level.upper()
        logging.getLogger().setLevel(level)
        logger.info(f"Log level updated to {level}")
        return {"message": f"Log level updated to {level}"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid log level: {str(e)}") 