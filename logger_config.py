import logging
from colorlog import ColoredFormatter

def setup_logger():
    """
    Configures a global logger for the entire program with colored logs.

    The logger outputs colored logs to the console and plain logs to a file.
    """
    # Format for console logs with colors
    console_format = (
        "%(log_color)s%(asctime)s - %(levelname)s - %(message)s%(reset)s"
    )

    # Format for file logs (without colors)
    file_format = "%(asctime)s - %(levelname)s - %(message)s"

    # Create a console formatter with colors
    console_formatter = ColoredFormatter(
        console_format,
        datefmt="%Y-%m-%d %H:%M:%S",
        log_colors={
            'DEBUG': 'cyan',
            'INFO': 'green',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'red,bg_white',
        }
    )

    # Create a file formatter (no colors)
    file_formatter = logging.Formatter(file_format)

    # Configure handlers
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(console_formatter)

    file_handler = logging.FileHandler("app.log")
    file_handler.setFormatter(file_formatter)

    # Configure the logger
    logging.basicConfig(
        level=logging.INFO,
        handlers=[console_handler, file_handler]
    )