import logging
import re
import sys
from typing import Any

# Regex pattern to identify and redact sensitive API keys or tokens in logs
SECRET_PATTERNS = [
    re.compile(r'(sk-[a-zA-Z0-9_-]{20,})'),
    re.compile(r'(AIzaSy[a-zA-Z0-9_-]{33})'),
    re.compile(r'(Bearer\s+[a-zA-Z0-9_\-\.]{20,})', re.IGNORECASE),
    re.compile(r'(password\s*[:=]\s*["\']?)([^"\'\s]+)(["\']?)', re.IGNORECASE),
]

class RedactingFormatter(logging.Formatter):
    """Logging formatter that automatically masks API keys, secrets, and passwords."""
    
    def format(self, record: logging.LogRecord) -> str:
        original = super().format(record)
        redacted = original
        for pattern in SECRET_PATTERNS:
            redacted = pattern.sub(r'***REDACTED_SECRET***', redacted)
        return redacted

def setup_logger(name: str = "assistant", log_level: int = logging.INFO) -> logging.Logger:
    """Configures and returns a secure, redacted application logger."""
    logger = logging.getLogger(name)
    logger.setLevel(log_level)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(log_level)
        formatter = RedactingFormatter(
            fmt="[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger
