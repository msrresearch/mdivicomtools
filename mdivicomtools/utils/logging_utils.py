# mdivicomtools/utils/logging_utils.py

import logging
from logging.config import dictConfig
from typing import Optional, Dict

# Some useful “preset” logging configurations for quick use
PRESET_CONFIGS = {
    "console_debug": {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {
                "format": "%(asctime)s %(levelname)-8s %(name)s - %(message)s"
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "standard",
                "level": "DEBUG",
                "stream": "ext://sys.stdout"
            }
        },
        "root": {
            "level": "DEBUG",
            "handlers": ["console"]
        }
    },
    "console_info_file_debug": {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {
                "format": "%(asctime)s %(levelname)-8s %(name)s - %(message)s"
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "standard",
                "level": "INFO",
                "stream": "ext://sys.stdout"
            },
            "debug_file": {
                "class": "logging.FileHandler",
                "formatter": "standard",
                "level": "DEBUG",
                "filename": "mdivicomtools_debug.log"
            }
        },
        "root": {
            "level": "DEBUG",
            "handlers": ["console", "debug_file"]
        }
    },
    "json_console_debug": {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "json": {
                "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
                "fmt": "%(asctime)s %(levelname)s %(name)s %(message)s"
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "json",
                "level": "DEBUG",
                "stream": "ext://sys.stdout"
            }
        },
        "root": {
            "level": "DEBUG",
            "handlers": ["console"]
        }
    }
}


def setup_logging(
        level: int = logging.INFO,
        format_string: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        preset: Optional[str] = None,
        dict_config_override: Optional[Dict] = None,
        date_format: Optional[str] = None,
) -> None:
    """
    A flexible logging setup function that can:
    1. Use one of the preset dictionary configs,
    2. Use a user-provided dictionary config (dict_config_override), or
    3. Fall back to a basicConfig approach with given level/format_string/date_format.

    Args:
        level (int): Fallback logging level if neither preset nor dict_config_override is used.
        format_string (str): Fallback logging format string for basicConfig.
        preset (str, optional): Key of a PRESET_CONFIGS dictionary for a quick, pre-built config.
        dict_config_override (Dict, optional): A full logging config dict to override any other settings.
        date_format (str, optional): Date format for the fallback basicConfig approach.
    """
    if dict_config_override:
        # Highest priority: use the user’s fully custom dictionary config
        dictConfig(dict_config_override)
        return

    if preset and preset in PRESET_CONFIGS:
        # Second priority: use one of our preset configs
        dictConfig(PRESET_CONFIGS[preset])
        return

    # Otherwise, do a simple basicConfig
    logging.basicConfig(
        level=level,
        format=format_string,
        datefmt=date_format
    )