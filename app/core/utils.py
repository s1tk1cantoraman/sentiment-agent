from typing import Optional
from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    ToolMessage,
)
from langchain_core.messages import (
    ChatMessage as LangchainChatMessage,
)
from functools import wraps
from pydantic import BaseModel
from starlette import status
import logging

from schema import ChatMessage

class ValidationError(BaseModel):
    message: str
    members: list[str] = []

class Error(BaseModel):
    code: Optional[str] = None
    message: str
    details: Optional[str] = None
    data: Optional[dict] = None
    validationErrors: Optional[list[ValidationError]] = None

class ErrorResponse(BaseModel):
    error: Error

class JSONResponseException(Exception):
    def __init__(self, status_code: int, message: str = None):
        self.status_code = status_code
        self.content = ErrorResponse(error={"message": message}).model_dump()



def convert_message_content_to_string(content: str | list[str | dict]) -> str:
    if isinstance(content, str):
        return content
    text: list[str] = []
    for content_item in content:
        if isinstance(content_item, str):
            text.append(content_item)
            continue
        if content_item["type"] == "text":
            text.append(content_item["text"])
    return "".join(text)


def langchain_to_chat_message(message: BaseMessage) -> ChatMessage:
    """Create a ChatMessage from a LangChain message."""
    match message:
        case HumanMessage():
            human_message = ChatMessage(
                type="human",
                content=convert_message_content_to_string(message.content),
            )
            return human_message
        case AIMessage():
            ai_message = ChatMessage(
                type="ai",
                content=convert_message_content_to_string(message.content),
            )
            if message.tool_calls:
                ai_message.tool_calls = message.tool_calls
            if message.response_metadata:
                ai_message.response_metadata = message.response_metadata
            return ai_message
        case ToolMessage():
            tool_message = ChatMessage(
                type="tool",
                content=convert_message_content_to_string(message.content),
                tool_call_id=message.tool_call_id,
            )
            return tool_message
        case LangchainChatMessage():
            if message.role == "custom":
                custom_message = ChatMessage(
                    type="custom",
                    content="",
                    custom_data=message.content[0],
                )
                return custom_message
            else:
                raise ValueError(f"Unsupported chat message role: {message.role}")
        case _:
            raise ValueError(f"Unsupported message type: {message.__class__.__name__}")


def remove_tool_calls(content: str | list[str | dict]) -> str | list[str | dict]:
    """Remove tool calls from content."""
    if isinstance(content, str):
        return content
    # Currently only Anthropic models stream tool calls, using content item type tool_use.
    return [
        content_item
        for content_item in content
        if isinstance(content_item, str) or content_item["type"] != "tool_use"
    ]
    
class CoreUtils:

    @staticmethod
    def exception_handling_decorator(func):
        logger = logging.getLogger(__name__)
        
        @wraps(func)
        def wrap(*args, **kwargs):
            try:
                logger.debug(f"Calling {func.__name__} with args: {args}, kwargs: {kwargs}")
                result = func(*args, **kwargs)
                logger.debug(f"{func.__name__} completed successfully")
                return result
            except (Exception, JSONResponseException) as e:
                logger.error(f"Error in {func.__name__}: {str(e)}", exc_info=True)
                if type(e) is JSONResponseException:
                    raise e
                else:
                    raise JSONResponseException(status.HTTP_500_INTERNAL_SERVER_ERROR,
                                                f"An unexpected error has occured.  {str(e)}")

        return wrap

    @staticmethod
    def aexception_handling_decorator(func):
        logger = logging.getLogger(__name__)
        
        @wraps(func)
        async def wrap(*args, **kwargs):
            try:
                logger.debug(f"Calling {func.__name__} with args: {args}, kwargs: {kwargs}")
                result = await func(*args, **kwargs)
                logger.debug(f"{func.__name__} completed successfully")
                return result
            except (Exception, JSONResponseException) as e:
                logger.error(f"Error in {func.__name__}: {str(e)}", exc_info=True)
                if type(e) is JSONResponseException:
                    raise e
                else:
                    raise JSONResponseException(status.HTTP_500_INTERNAL_SERVER_ERROR,
                                                f"An unexpected error has occured.  {str(e)}")

        return wrap 
