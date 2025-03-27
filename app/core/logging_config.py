import logging
import sys
from typing import  Optional
import os

from core.db_logging import AsyncDBLogHandler

def setup_logging(log_level: str = "INFO", db_path: Optional[str] = None) -> None:
    """Configure logging for the application."""
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Remove existing handlers to avoid duplicates
    root_logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # Database handler
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    if db_path is None:
        db_path = f"{log_dir}/logs.db"
    
    try:
        db_handler = AsyncDBLogHandler(db_path=db_path)
        db_handler.setFormatter(formatter)
        root_logger.addHandler(db_handler)
        console_handler.setLevel(logging.INFO)  # Set console to INFO level
        db_handler.setLevel(logging.DEBUG)  # But capture all details in the database
    except Exception as e:
        # Fall back to file-based logging if database handler fails
        from logging.handlers import RotatingFileHandler
        print(f"Failed to initialize database logging: {e}. Falling back to file logging.")
        file_handler = RotatingFileHandler(
            f'{log_dir}/app.log',
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    # Set logging levels for third-party libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    
    logger = logging.getLogger(__name__)
    logger.info("Logging system initialized") 