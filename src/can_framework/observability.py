"""Structured logging helpers for CAN automation tests."""

from __future__ import annotations

import json
import logging
import os
import uuid
from datetime import datetime, timezone
from typing import Any, Mapping

STANDARD_LOG_RECORD_FIELDS = frozenset(logging.makeLogRecord({}).__dict__.keys())


def get_default_log_context() -> dict[str, Any]:
    """Build a production-shaped default context for CAN test logs."""
    run_id = os.getenv("CAN_RUN_ID") or f"run-{uuid.uuid4().hex[:12]}"
    return {
        "run_id": run_id,
        "vehicle_program": os.getenv("CAN_VEHICLE_PROGRAM", "GENERIC_MULE"),
        "environment": os.getenv("CAN_ENVIRONMENT", "test-bench"),
        "component": os.getenv("CAN_COMPONENT", "can-framework"),
        "bus_channel": os.getenv("CAN_CHANNEL", "vcan0"),
        "can_interface": os.getenv("CAN_INTERFACE", "socketcan"),
        "job_name": os.getenv("CI_JOB_NAME", "local"),
        "build_id": os.getenv("CI_BUILD_ID", "local"),
    }


class AutomotiveLogFilter(logging.Filter):
    """Inject shared automotive context into log records."""

    def __init__(self, context: Mapping[str, Any] | None = None) -> None:
        super().__init__()
        self._context = dict(context or {})

    def filter(self, record: logging.LogRecord) -> bool:
        for key, value in self._context.items():
            if not hasattr(record, key):
                setattr(record, key, value)

        if not hasattr(record, "event_type"):
            record.event_type = "app.log"
        if not hasattr(record, "test_name"):
            record.test_name = "-"

        return True


class JsonLineFormatter(logging.Formatter):
    """Serialize log records as newline-delimited JSON."""

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc)
            .isoformat(timespec="milliseconds")
            .replace("+00:00", "Z"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "event_type": getattr(record, "event_type", "app.log"),
            "test_name": getattr(record, "test_name", "-"),
        }

        for key, value in record.__dict__.items():
            if key in STANDARD_LOG_RECORD_FIELDS or key in payload:
                continue
            payload[key] = _coerce_json_value(value)

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(payload, sort_keys=True)


def build_event_extra(event_type: str, **fields: Any) -> dict[str, Any]:
    """Create an `extra` payload with a consistent event_type field."""
    return {"event_type": event_type, **fields}


def format_can_id(arbitration_id: int | None) -> str | None:
    """Represent CAN IDs consistently for logs and prompts."""
    if arbitration_id is None:
        return None
    return f"0x{arbitration_id:X}"


def format_payload(data: Any) -> str:
    """Format a CAN payload as uppercase hex bytes separated by spaces."""
    if data is None:
        return ""
    return " ".join(f"{byte:02X}" for byte in data)


def message_to_log_fields(message: Any) -> dict[str, Any]:
    """Extract the most useful machine-readable fields from a CAN message."""
    arbitration_id = getattr(message, "arbitration_id", None)
    data = list(getattr(message, "data", []) or [])
    return {
        "arbitration_id": arbitration_id,
        "arbitration_id_hex": format_can_id(arbitration_id),
        "dlc": len(data),
        "payload_hex": format_payload(data),
        "is_extended_id": getattr(message, "is_extended_id", None),
    }


def _coerce_json_value(value: Any) -> Any:
    """Convert uncommon Python objects into JSON-safe values."""
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, bytes):
        return value.hex().upper()
    if isinstance(value, (list, tuple)):
        return [_coerce_json_value(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _coerce_json_value(item) for key, item in value.items()}
    return str(value)
