import logging
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

from core import settings
from schema.schema import ThreadDeleteResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/thread")

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

@router.delete("/{thread_id}")
async def delete_thread(thread_id: str) -> ThreadDeleteResponse:
    """
    Delete a thread and its associated data using the thread_id.
    """
    try:
        async with AsyncSqliteSaver.from_conn_string("checkpoints.db") as saver:
            # Delete all checkpoints associated with this thread_id
            await saver.adelete({"thread_id": thread_id})
            return ThreadDeleteResponse(
                success=True,
                message=f"Thread {thread_id} successfully deleted"
            )
    except Exception as e:
        logger.error(f"Error deleting thread {thread_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete thread: {str(e)}"
        ) 