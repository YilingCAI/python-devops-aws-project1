"""
Enterprise-grade structured logging configuration.

Features:
- Structured JSON logging for production
- Human-readable logging for development
- Log rotation for file outputs
- Request ID correlation
- Performance tracking
- Error tracking with context
"""

import logging
import sys
import os
from datetime import datetime
from typing import Dict, Any
from logging.handlers import RotatingFileHandler
from pythonjsonlogger import jsonlogger
from app.core.config import settings


class StructuredJsonFormatter(jsonlogger.JsonFormatter):
    """Custom JSON formatter with additional context."""

    def add_fields(
        self,
        log_record: Dict[str, Any],
        record: logging.LogRecord,
        message_dict: Dict[str, Any],
    ) -> None:
        """Add custom fields to log record."""
        super().add_fields(log_record, record, message_dict)

        # Add environment info
        log_record["environment"] = settings.ENVIRONMENT
        log_record["service"] = settings.PROJECT_NAME
        log_record["version"] = settings.APP_VERSION

        # Add timestamp
        log_record["timestamp"] = datetime.utcnow().isoformat()

        # Add request ID if available (from context)
        if hasattr(record, "request_id"):
            log_record["request_id"] = record.request_id

        # Add exception info with full traceback
        if record.exc_info:
            log_record["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": self.formatException(record.exc_info),
            }

        # Add performance metrics if available
        if hasattr(record, "duration_ms"):
            log_record["duration_ms"] = record.duration_ms

        if hasattr(record, "status_code"):
            log_record["status_code"] = record.status_code


class HumanReadableFormatter(logging.Formatter):
    """Human-readable formatter for development."""

    COLORS = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[41m",  # Red background
        "RESET": "\033[0m",  # Reset
    }

    def format(self, record: logging.LogRecord) -> str:
        """Format log record with colors."""
        if not settings.DEBUG:
            # Remove colors in production
            log_format = (
                "%(asctime)s - [%(levelname)s] - %(name)s:%(lineno)d - %(message)s"
            )
        else:
            # Add colors in development
            levelname = record.levelname
            color = self.COLORS.get(levelname, "")
            reset = self.COLORS["RESET"]

            log_format = (
                f"%(asctime)s - {color}[%(levelname)s]{reset} - "
                "%(name)s:%(lineno)d - %(message)s"
            )

        formatter = logging.Formatter(log_format, datefmt="%Y-%m-%d %H:%M:%S")
        return formatter.format(record)


def setup_logging() -> logging.Logger:
    """
    Setup production-grade logging configuration.

    Returns:
        logging.Logger: Configured root logger
    """
    root_logger = logging.getLogger()

    # Set log level based on environment
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    root_logger.setLevel(log_level)

    # Remove existing handlers
    root_logger.handlers = []

    # Console handler (always)
    console_handler = logging.StreamHandler(sys.stdout)

    # Configure formatter based on environment and setting
    if settings.LOG_FORMAT == "json":
        formatter = StructuredJsonFormatter()
    else:
        formatter = HumanReadableFormatter()

    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # File handler (if configured)
    if settings.LOG_OUTPUT == "file":
        setup_file_logging(root_logger, formatter)

    # Configure third-party loggers
    configure_third_party_logging(log_level)

    # Log startup info
    root_logger.info(
        "Logging initialized",
        extra={
            "environment": settings.ENVIRONMENT,
            "log_level": settings.LOG_LEVEL,
            "log_format": settings.LOG_FORMAT,
        },
    )

    return root_logger


def setup_file_logging(
    root_logger: logging.Logger,
    formatter: logging.Formatter,
) -> None:
    """
    Setup file-based logging with rotation.

    Args:
        root_logger: Root logger instance
        formatter: Log formatter to use
    """
    try:
        # Create log directory if it doesn't exist
        log_dir = settings.LOG_FILE_PATH
        os.makedirs(log_dir, exist_ok=True)

        # Create rotating file handler
        log_file = os.path.join(log_dir, "app.log")
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=settings.LOG_FILE_MAX_BYTES,  # 10MB by default
            backupCount=settings.LOG_FILE_BACKUP_COUNT,  # Keep 10 files
        )

        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

        root_logger.info(f"File logging configured: {log_file}")

    except Exception as e:
        root_logger.error(f"Failed to setup file logging: {e}")


def configure_third_party_logging(log_level: int) -> None:
    """
    Configure logging for third-party libraries.

    Args:
        log_level: Log level to apply
    """
    # SQLAlchemy
    logging.getLogger("sqlalchemy.engine").setLevel(log_level)
    logging.getLogger("sqlalchemy.pool").setLevel(log_level)

    # Uvicorn
    logging.getLogger("uvicorn").setLevel(log_level)
    logging.getLogger("uvicorn.access").setLevel(log_level)

    # FastAPI
    logging.getLogger("fastapi").setLevel(log_level)

    # Alembic
    logging.getLogger("alembic").setLevel(log_level)


def get_logger(name: str) -> logging.Logger:
    """
    Get a named logger instance.

    Usage:
        from app.core.logging import get_logger
        logger = get_logger(__name__)
        logger.info("Application started")

    Args:
        name: Logger name (typically __name__)

    Returns:
        logging.Logger: Configured logger
    """
    return logging.getLogger(name)


class LoggingContext:
    """
    Context manager for adding contextual information to logs.

    Usage:
        with LoggingContext(request_id=str(uuid4()), user_id=123):
            logger.info("Processing request")
    """

    def __init__(self, **context_vars):
        """Initialize with context variables."""
        self.context_vars = context_vars
        self.old_values = {}

    def __enter__(self):
        """Enter context and set context variables."""
        for key, value in self.context_vars.items():
            # Store old value if it exists
            if hasattr(logging, key):
                self.old_values[key] = getattr(logging, key)
            # Set new value
            setattr(logging, key, value)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context and restore old values."""
        for key in self.context_vars:
            if key in self.old_values:
                setattr(logging, key, self.old_values[key])
            else:
                delattr(logging, key)
        return False
