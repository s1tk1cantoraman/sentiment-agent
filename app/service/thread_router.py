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
    logger.info(f"Attempting to delete thread {thread_id}")
    try:
        async with AsyncSqliteSaver.from_conn_string("checkpoints.db") as saver:
            # Access the underlying SQLite connection
            conn = saver.conn
            
            # Delete all checkpoints for this thread_id
            async with conn.execute(
                "DELETE FROM checkpoints WHERE thread_id = ?",
                (thread_id,)
            ):
                pass
                
            # Delete all writes for this thread_id
            async with conn.execute(
                "DELETE FROM writes WHERE thread_id = ?",
                (thread_id,)
            ):
                pass
                
            # Commit the changes
            await conn.commit()
            
            logger.info(f"Thread {thread_id} successfully deleted from database")
            return ThreadDeleteResponse(
                success=True,
                message=f"Thread {thread_id} successfully deleted"
            )
    except Exception as e:
        logger.error(f"Error deleting thread {thread_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete thread: {str(e)}"
        ) 