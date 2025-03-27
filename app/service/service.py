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
from service.thread_router import router as thread_router
from core.logging_config import setup_logging
from service.logging_router import router as logging_router
import logging

warnings.filterwarnings("ignore", category=LangChainBetaWarning)

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Lifecycle manager for the FastAPI application."""
    logger.info("Starting application...")
    
    # Setup logging first
    setup_logging(settings.LOG_LEVEL)
    logger.info(f"Logging configured with level: {settings.LOG_LEVEL}")
    
    # Initialize checkpointer
    try:
        async with AsyncSqliteSaver.from_conn_string("checkpoints.db") as saver:
            logger.info("Initializing agents...")
            agents = get_all_agent_info()
            for a in agents:
                agent = get_agent(a.key)
                agent.checkpointer = saver
                logger.debug(f"Agent {a.key} initialized with checkpointer")
            logger.info("Application startup complete")
            yield
    except Exception as e:
        logger.error(f"Failed to initialize application: {e}")
        raise

app = FastAPI(lifespan=lifespan)

@app.get("/info")
async def info() -> ServiceMetadata:
    logger.debug("Fetching service metadata")
    models = list(settings.AVAILABLE_MODELS)
    models.sort()
    metadata = ServiceMetadata(
        agents=get_all_agent_info(),
        models=models,
        default_agent=DEFAULT_AGENT,
        default_model=settings.DEFAULT_MODEL,
    )
    logger.debug(f"Returning metadata: {metadata}")
    return metadata

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    logger.debug("Health check requested")
    return {"status": "ok"}

app.include_router(inference_router)
app.include_router(history_router)
app.include_router(thread_router)
app.include_router(logging_router)
