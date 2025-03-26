import warnings
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from fastapi import FastAPI
from langchain_core._api import LangChainBetaWarning
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from agents.agents import get_agent, get_all_agent_info, DEFAULT_AGENT
from core import settings
from schema import ServiceMetadata
from service.inference_router import router as inference_router
from service.history_router import router as history_router

warnings.filterwarnings("ignore", category=LangChainBetaWarning)

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    async with AsyncSqliteSaver.from_conn_string("checkpoints.db") as saver:
        agents = get_all_agent_info()
        for a in agents:
            agent = get_agent(a.key)
            agent.checkpointer = saver
        yield

app = FastAPI(lifespan=lifespan)

@app.get("/info")
async def info() -> ServiceMetadata:
    models = list(settings.AVAILABLE_MODELS)
    models.sort()
    return ServiceMetadata(
        agents=get_all_agent_info(),
        models=models,
        default_agent=DEFAULT_AGENT,
        default_model=settings.DEFAULT_MODEL,
    )

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}

app.include_router(inference_router)
app.include_router(history_router)
