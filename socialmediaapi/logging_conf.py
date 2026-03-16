from logging.config import dictConfig

from socialmediaapi.config import DevConfig, config


def configure_logging():
    dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "console": {
                    "class": "logging.Formatter",
                    "datefmt": "%Y-%m-%dT%H:%M:%S",
                    "format": "%(name)s:%(lineno)d - %(message)s",
                },
                "file": {
                    "class": "logging.Formatter",
                    "datefmt": "%Y-%m-%dT%H:%M:%S",
                    "format": "%(asctime)s.%(msecs)03dZ | %(levelname)-8s | - %(name)s:%(lineno)d - %(message)s",
                },
            },
            "handlers": {
                "default": {
                    "class": "rich.logging.RichHandler",
                    "level": "DEBUG",
                    "formatter": "console",
                },
                "rotating_file": {
                    "class": "logging.handlers.RotatingFileHandler",
                    "level": "DEBUG",
                    "formatter": "file",
                    "filename": "socialmediaapi.log",
                    "maxBytes": 1024 * 1024,  # 1 MB
                    "backupCount": 5,
                    "encoding": "utf-8",
                },
            },
            "loggers": {
                "uvicorn": {
                    "level": "INFO",
                    "handlers": ["default", "rotating_file"],
                },
                "socialmediaapi": {
                    "level": "DEBUG" if isinstance(config, DevConfig) else "INFO",
                    "handlers": ["default", "rotating_file"],
                    "propagate": False,
                },
                "databases": {
                    "level": "WARNING",
                    "handlers": ["default", "rotating_file"],
                },
                "aiomysql": {
                    "level": "WARNING",
                    "handlers": ["default", "rotating_file"],
                },
            },
        }
    )
