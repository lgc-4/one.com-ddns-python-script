# modules/logger.py
import logging

GRAY = '\033[90m'
RED = '\033[91m'
YELLOW = '\033[93m'
RESET = '\033[0m'

class ColoredFormatter(logging.Formatter):
    """A formatter that adds colors based on log level."""

    def format(self, record):
        log_level = record.levelname
        if log_level == "DEBUG":
            log_level_colored = f"{GRAY}[DEBUG]{RESET}"
        elif log_level == "WARNING":
            log_level_colored = f"{YELLOW}[WARN]{RESET}"
        elif log_level == "ERROR":
            log_level_colored = f"{RED}[ERROR]{RESET}"
        else:
            log_level_colored = f"[{log_level}]"  # No color for INFO

        return logging.Formatter(f'{log_level_colored} %(message)s').format(record)

def setup_logging(level=logging.INFO):
    """Sets up centralized logging for the application."""
    formatter = ColoredFormatter()
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)

    logger = logging.getLogger("one_com_ddns")
    logger.setLevel(level)
    logger.addHandler(handler)

    return logger