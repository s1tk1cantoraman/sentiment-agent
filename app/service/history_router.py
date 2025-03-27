import logging
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from langchain_core.messages import AnyMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph.state import CompiledStateGraph

from agents.agents import DEFAULT_AGENT, get_agent
from core import settings
from schema import ChatHistory, ChatHistoryInput, ChatMessage
from core.utils import langchain_to_chat_message, CoreUtils

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/history")

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

@router.post("")
@CoreUtils.exception_handling_decorator
def history(input: ChatHistoryInput) -> ChatHistory:
    """
    Get chat history.
    """
    agent: CompiledStateGraph = get_agent(DEFAULT_AGENT)
    state_snapshot = agent.get_state(
        config=RunnableConfig(
            configurable={
                "thread_id": input.thread_id,
            }
        )
    )
    messages: list[AnyMessage] = state_snapshot.values["messages"]
    chat_messages: list[ChatMessage] = [langchain_to_chat_message(m) for m in messages]
    return ChatHistory(messages=chat_messages) 