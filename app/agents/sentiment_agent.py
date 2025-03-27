from typing import  Literal
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, SystemMessage
from langchain_core.runnables import RunnableConfig, RunnableLambda, RunnableSerializable
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, MessagesState, StateGraph

from core import get_model, settings




SYSTEM_PROMPT = """
You are a sentiment analysis agent.
You will be given a text of product reviews, and you need to analyze the sentiment of the text.
You must classify the sentiment as exactly one of these values: "positive", "neutral", or "negative".
Do not provide any additional explanation - only return the sentiment classification.
"""


def wrap_model(model: BaseChatModel) -> RunnableSerializable[MessagesState, AIMessage]:
    # model = model.bind_tools(tools)
    preprocessor = RunnableLambda(
                    lambda state: [SystemMessage(content=SYSTEM_PROMPT)] + state["messages"],
                    name="StateModifier",
                    )
    return preprocessor | model

async def acall_model(state: MessagesState, config: RunnableConfig) -> MessagesState:
    m = get_model(config["configurable"].get("model", settings.DEFAULT_MODEL))
    model_runnable = wrap_model(m)
    response = await model_runnable.ainvoke(state, config)

    # We return a list, because this will get added to the existing list
    return {"messages": [response]}


# After "model", if there are tool calls, run "tools". Otherwise END.
def pending_tool_calls(state: MessagesState) -> Literal["tools", "done"]:
    last_message = state["messages"][-1]
    if not isinstance(last_message, AIMessage):
        raise TypeError(f"Expected AIMessage, got {type(last_message)}")
    if last_message.tool_calls:
        return "tools"
    return "done"


# Define the graph
agent = StateGraph(MessagesState)
agent.add_node("model", acall_model)
agent.set_entry_point("model")
# agent.add_node("tools", ToolNode(tools))


agent.add_edge("model", END)
# agent.add_edge("tools", "model")
# agent.add_conditional_edges("model", pending_tool_calls, {"tools": "tools", "done": END})


sentiment_agent = agent.compile(checkpointer=MemorySaver())


# display(Image(sentiment_agent.get_graph(xray=True).draw_mermaid_png()))
