"""Pytest bootstrap for local imports and test-run logging."""

from __future__ import annotations

import logging
import os
import sys
from datetime import datetime
from pathlib import Path

import pytest
from _pytest.reports import TestReport

# Make the repository root importable so tests can import from src/.
ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from can_framework.observability import (  # noqa: E402
    AutomotiveLogFilter,
    JsonLineFormatter,
    build_event_extra,
    get_default_log_context,
)

CURRENT_TEST = "-"
RUN_CONTEXT: dict[str, object] = {}


class LogContextFilter(logging.Filter):
    """Inject the current pytest test node id into each log record."""

    def filter(self, record: logging.LogRecord) -> bool:
        if not hasattr(record, "test_name"):
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


def _get_log_format(env_var: str, default: str) -> str:
    """Resolve a supported log output format."""
    value = os.getenv(env_var, default).strip().lower()
    return value if value in {"text", "json"} else default


def _resolve_log_file(log_dir: Path, file_format: str) -> Path:
    """Create a timestamped log file unless one is explicitly requested."""
    log_file_name = os.getenv("PYTEST_LOG_FILE")
    if not log_file_name:
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        suffix = "jsonl" if file_format == "json" else "log"
        log_file_name = f"pytest-{timestamp}.{suffix}"
    return log_dir / log_file_name


def _remove_existing_test_handlers(logger: logging.Logger) -> None:
    """Avoid duplicate handlers across repeated pytest runs in the same process."""
    for handler in list(logger.handlers):
        if getattr(handler, "_can_test_logging", False):
            logger.removeHandler(handler)
            handler.close()


def pytest_configure(config: pytest.Config) -> None:
    """Configure project-wide logging for pytest runs."""
    global RUN_CONTEXT

    log_dir = _resolve_log_dir()
    console_format = _get_log_format("PYTEST_CONSOLE_LOG_FORMAT", "text")
    file_format = _get_log_format("PYTEST_FILE_LOG_FORMAT", os.getenv("PYTEST_LOG_FORMAT", "json"))
    log_file = _resolve_log_file(log_dir, file_format)
    RUN_CONTEXT = get_default_log_context()

    root_level = logging.DEBUG
    console_level = _get_log_level("PYTEST_CONSOLE_LOG_LEVEL", "INFO")
    file_level = _get_log_level("PYTEST_FILE_LOG_LEVEL", "DEBUG")

    logger = logging.getLogger()
    logger.setLevel(root_level)

    text_console_formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(event_type)s | %(test_name)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    text_file_formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(event_type)s | %(test_name)s | %(name)s | %(filename)s:%(lineno)d | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    _remove_existing_test_handlers(logger)

    console = logging.StreamHandler(sys.stdout)
    console.setLevel(console_level)
    console.setFormatter(JsonLineFormatter() if console_format == "json" else text_console_formatter)
    console.addFilter(LogContextFilter())
    console.addFilter(AutomotiveLogFilter(RUN_CONTEXT))
    console._can_test_logging = True  # type: ignore[attr-defined]

    file_handler = logging.FileHandler(log_file, mode="w", encoding="utf-8", delay=True)
    file_handler.setLevel(file_level)
    file_handler.setFormatter(JsonLineFormatter() if file_format == "json" else text_file_formatter)
    file_handler.addFilter(LogContextFilter())
    file_handler.addFilter(AutomotiveLogFilter(RUN_CONTEXT))
    file_handler._can_test_logging = True  # type: ignore[attr-defined]

    logger.addHandler(console)
    logger.addHandler(file_handler)
    config._can_test_log_handlers = [console, file_handler]  # type: ignore[attr-defined]
    config._can_test_log_file = log_file  # type: ignore[attr-defined]
    config._can_test_run_context = RUN_CONTEXT  # type: ignore[attr-defined]

    # Capture warnings emitted through the warnings module into the configured logs.
    logging.captureWarnings(True)

    # Keep common third-party libraries from flooding CI logs while still preserving
    # useful application-level debug messages in the file log.
    logging.getLogger("urllib3").setLevel(_get_log_level("PYTEST_URLLIB3_LOG_LEVEL", "INFO"))
    logging.getLogger(__name__).info(
        "Configured pytest logging",
        extra=build_event_extra(
            "pytest.session.configured",
            log_file=str(log_file),
            file_format=file_format,
            console_format=console_format,
        ),
    )


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


def pytest_sessionstart(session: pytest.Session) -> None:
    """Emit a structured event at the beginning of the test session."""
    logging.getLogger(__name__).info(
        "Pytest session started",
        extra=build_event_extra("pytest.session.started", test_count=session.testscollected),
    )


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    """Emit a structured event when the test session completes."""
    logging.getLogger(__name__).info(
        "Pytest session finished",
        extra=build_event_extra(
            "pytest.session.finished",
            exitstatus=exitstatus,
            test_count=session.testscollected,
            log_file=str(getattr(session.config, "_can_test_log_file", "-")),
        ),
    )


def pytest_runtest_logreport(report: TestReport) -> None:
    """Emit one structured event for each reported test phase outcome."""
    if report.passed and report.when != "call":
        return

    if report.passed:
        level = logging.INFO
        outcome = "passed"
    elif report.failed:
        level = logging.ERROR
        outcome = "failed"
    else:
        level = logging.WARNING
        outcome = "skipped"

    summary = None
    if report.failed and hasattr(report, "longreprtext"):
        lines = [line.strip() for line in report.longreprtext.splitlines() if line.strip()]
        summary = lines[-1] if lines else report.outcome
    elif report.skipped:
        summary = str(report.longrepr[2]) if isinstance(report.longrepr, tuple) else report.outcome

    logging.getLogger(__name__).log(
        level,
        "Pytest test phase completed",
        extra=build_event_extra(
            f"pytest.test.{outcome}",
            test_name=report.nodeid,
            phase=report.when,
            duration_s=round(report.duration, 6),
            outcome=outcome,
            summary=summary,
        ),
    )
