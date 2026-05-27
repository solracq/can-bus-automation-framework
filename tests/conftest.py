"""Pytest bootstrap for local imports and test-run logging."""

from __future__ import annotations

import logging
import os
import sys
from datetime import datetime
from pathlib import Path

import pytest

# Make the repository root importable so tests can import from src/.
ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

CURRENT_TEST = "-"


class LogContextFilter(logging.Filter):
    """Inject the current pytest test node id into each log record."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.test_name = CURRENT_TEST
        return True


def _get_log_level(env_var: str, default: str) -> int:
    """Resolve a logging level from an environment variable."""
    level_name = os.getenv(env_var, default).upper()
    return getattr(logging, level_name, getattr(logging, default.upper()))


def _resolve_log_dir() -> Path:
    """Create the default per-run log directory."""
    log_dir_setting = Path(os.getenv("PYTEST_LOG_DIR", "log"))
    log_dir = log_dir_setting if log_dir_setting.is_absolute() else ROOT / log_dir_setting
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir


def _resolve_log_file(log_dir: Path) -> Path:
    """Create a timestamped log file unless one is explicitly requested."""
    log_file_name = os.getenv("PYTEST_LOG_FILE")
    if not log_file_name:
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        log_file_name = f"pytest-{timestamp}.log"
    return log_dir / log_file_name


def _remove_existing_test_handlers(logger: logging.Logger) -> None:
    """Avoid duplicate handlers across repeated pytest runs in the same process."""
    for handler in list(logger.handlers):
        if getattr(handler, "_can_test_logging", False):
            logger.removeHandler(handler)
            handler.close()


def pytest_configure(config: pytest.Config) -> None:
    """Configure project-wide logging for pytest runs."""
    log_dir = _resolve_log_dir()
    log_file = _resolve_log_file(log_dir)

    root_level = logging.DEBUG
    console_level = _get_log_level("PYTEST_CONSOLE_LOG_LEVEL", "INFO")
    file_level = _get_log_level("PYTEST_FILE_LOG_LEVEL", "DEBUG")

    logger = logging.getLogger()
    logger.setLevel(root_level)

    console_formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(test_name)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(test_name)s | %(name)s | %(filename)s:%(lineno)d | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    _remove_existing_test_handlers(logger)

    console = logging.StreamHandler(sys.stdout)
    console.setLevel(console_level)
    console.setFormatter(console_formatter)
    console.addFilter(LogContextFilter())
    console._can_test_logging = True  # type: ignore[attr-defined]

    file_handler = logging.FileHandler(log_file, mode="w", encoding="utf-8", delay=True)
    file_handler.setLevel(file_level)
    file_handler.setFormatter(file_formatter)
    file_handler.addFilter(LogContextFilter())
    file_handler._can_test_logging = True  # type: ignore[attr-defined]

    logger.addHandler(console)
    logger.addHandler(file_handler)
    config._can_test_log_handlers = [console, file_handler]  # type: ignore[attr-defined]

    # Capture warnings emitted through the warnings module into the configured logs.
    logging.captureWarnings(True)

    # Keep common third-party libraries from flooding CI logs while still preserving
    # useful application-level debug messages in the file log.
    logging.getLogger("urllib3").setLevel(_get_log_level("PYTEST_URLLIB3_LOG_LEVEL", "INFO"))

def pytest_unconfigure(config: pytest.Config) -> None:
    """Close file handles and remove test-specific handlers after the run."""
    logger = logging.getLogger()
    for handler in getattr(config, "_can_test_log_handlers", []):
        logger.removeHandler(handler)
        handler.close()


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_protocol(item: pytest.Item, nextitem: pytest.Item | None):
    """Attach the current test node id to log records during the test lifecycle."""
    global CURRENT_TEST

    _ = nextitem
    previous_test = CURRENT_TEST
    CURRENT_TEST = item.nodeid
    try:
        yield
    finally:
        CURRENT_TEST = previous_test
