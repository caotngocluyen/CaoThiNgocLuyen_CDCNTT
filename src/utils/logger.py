import logging
import sys
from pathlib import Path

def get_logger(name: str = "LegalChatbot", log_file: str = "app.log") -> logging.Logger:
    """
    Returns a configured logger with console and file handlers.
    """
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)

    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] [%(name)s]: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Console Handler (UTF-8 safe for Windows console)
    try:
        import io
        utf8_stream = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
        console_handler = logging.StreamHandler(utf8_stream)
    except Exception:
        console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File Handler
    try:
        from config import LOGS_DIR
        log_path = LOGS_DIR / log_file
    except Exception:
        log_path = Path("logs") / log_file
        log_path.parent.mkdir(parents=True, exist_ok=True)

    file_handler = logging.FileHandler(str(log_path), encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger
