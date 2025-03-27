import asyncio
import logging
import sqlite3
import sys
import threading
import time
from dataclasses import dataclass
from datetime import datetime
from logging.handlers import QueueHandler, QueueListener
from queue import Queue
from typing import Any, Dict, List, Optional


@dataclass
class LogRecord:
    timestamp: str
    level: str
    logger_name: str
    message: str
    exc_info: Optional[str] = None
    thread_name: Optional[str] = None
    process_name: Optional[str] = None
    extra: Optional[Dict[str, Any]] = None


class AsyncDBLogHandler(logging.Handler):
    """
    A logging handler that asynchronously writes log records to a SQLite database.
    Uses a queue and background thread to ensure non-blocking operation.
    """
    
    def __init__(self, db_path: str = "logs.db", queue_size: int = 1000):
        super().__init__()
        self.db_path = db_path
        self.queue: Queue = Queue(maxsize=queue_size)
        self._initialize_db()
        
        # Set up the queue handler and listener
        self.queue_handler = QueueHandler(self.queue)
        
        # Create a proper handler class for the db_handler
        class DBHandler(logging.Handler):
            def __init__(self, parent):
                super().__init__()
                self.parent = parent
                
            def emit(self, record):
                self.parent._db_handler(record)
                
        # Use the proper handler class
        self.db_handler = DBHandler(self)
        self.listener = QueueListener(
            self.queue, 
            self.db_handler,
            respect_handler_level=True
        )
        self.listener.start()
        
        # Keep track of event loop for potential async operations
        self._loop = None
        
    def _initialize_db(self) -> None:
        """Initialize the SQLite database and create tables if they don't exist."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create logs table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            level TEXT NOT NULL,
            logger_name TEXT NOT NULL,
            message TEXT NOT NULL,
            exc_info TEXT,
            thread_name TEXT,
            process_name TEXT,
            extra TEXT
        )
        ''')
        
        # Create index on timestamp and level for faster queries
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON logs (timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_level ON logs (level)')
        
        conn.commit()
        conn.close()
    
    def _db_handler(self, record: logging.LogRecord) -> None:
        """Write a log record to the database."""
        try:
            # Convert record to our custom format
            log_record = LogRecord(
                timestamp=datetime.fromtimestamp(record.created).isoformat(),
                level=record.levelname,
                logger_name=record.name,
                message=record.getMessage(),
                exc_info=record.exc_text if record.exc_text else None,
                thread_name=record.threadName,
                process_name=record.processName,
                extra={k: v for k, v in record.__dict__.items() 
                      if k not in ['args', 'exc_info', 'exc_text', 'message', 'msg', 'levelname', 
                                  'levelno', 'pathname', 'filename', 'module', 'lineno', 'funcName', 
                                  'created', 'msecs', 'relativeCreated', 'name', 'threadName', 
                                  'processName', 'thread', 'process']} if hasattr(record, '__dict__') else None
            )
            
            # Connect to the database and insert the record
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
            INSERT INTO logs (timestamp, level, logger_name, message, exc_info, thread_name, process_name, extra)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                log_record.timestamp,
                log_record.level,
                log_record.logger_name,
                log_record.message,
                log_record.exc_info,
                log_record.thread_name,
                log_record.process_name,
                str(log_record.extra) if log_record.extra else None
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            # If we fail to log to the database, print to stderr as a fallback
            print(f"Error writing to log database: {e}", file=sys.stderr)
    
    def emit(self, record: logging.LogRecord) -> None:
        """Send the log record to the queue handler."""
        self.queue_handler.emit(record)
    
    def close(self) -> None:
        """Stop the queue listener when the handler is closed."""
        self.listener.stop()
        super().close()


class AsyncDBLogger:
    """
    Utility class for working with the database logs.
    Provides methods to query and analyze logs.
    """
    
    def __init__(self, db_path: str = "logs.db"):
        self.db_path = db_path
    
    def get_logs(self, 
                 level: Optional[str] = None, 
                 start_time: Optional[str] = None, 
                 end_time: Optional[str] = None, 
                 logger_name: Optional[str] = None,
                 limit: int = 100) -> List[LogRecord]:
        """Query logs from the database with optional filters."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = "SELECT timestamp, level, logger_name, message, exc_info, thread_name, process_name, extra FROM logs WHERE 1=1"
        params = []
        
        if level:
            query += " AND level = ?"
            params.append(level)
        
        if start_time:
            query += " AND timestamp >= ?"
            params.append(start_time)
        
        if end_time:
            query += " AND timestamp <= ?"
            params.append(end_time)
        
        if logger_name:
            query += " AND logger_name = ?"
            params.append(logger_name)
        
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        logs = []
        for row in rows:
            logs.append(LogRecord(
                timestamp=row[0],
                level=row[1],
                logger_name=row[2],
                message=row[3],
                exc_info=row[4],
                thread_name=row[5],
                process_name=row[6],
                extra=eval(row[7]) if row[7] else None
            ))
        
        conn.close()
        return logs
    
    def clear_old_logs(self, days: int = 30) -> int:
        """Delete logs older than the specified number of days."""
        from datetime import datetime, timedelta
        
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM logs WHERE timestamp < ?", (cutoff_date,))
        deleted_count = cursor.rowcount
        
        conn.commit()
        conn.close()
        
        return deleted_count 