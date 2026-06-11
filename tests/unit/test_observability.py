"""Unit tests for structured logging helpers."""

from __future__ import annotations

import json
import logging
from types import SimpleNamespace

import pytest

from can_framework.observability import (
    AutomotiveLogFilter,
    JsonLineFormatter,
    build_event_extra,
    format_can_id,
    format_payload,
    message_to_log_fields,
)

pytestmark = pytest.mark.unit


def test_json_formatter_serializes_structured_fields() -> None:
    logger = logging.getLogger("tests.observability")
    record = logger.makeRecord(
        "tests.observability",
        logging.INFO,
        __file__,
        10,
        "hello %s",
        ("world",),
        None,
        extra=build_event_extra("can.tx", trace_id="trace-123", payload_hex="AA"),
    )
    AutomotiveLogFilter(
        {
            "run_id": "run-123",
            "vehicle_program": "MULE_X",
            "environment": "rig",
            "component": "ecu-tests",
            "bus_channel": "vcan0",
            "can_interface": "socketcan",
        }
    ).filter(record)

    payload = json.loads(JsonLineFormatter().format(record))

    assert payload["message"] == "hello world"
    assert payload["event_type"] == "can.tx"
    assert payload["run_id"] == "run-123"
    assert payload["trace_id"] == "trace-123"
    assert payload["payload_hex"] == "AA"


def test_message_to_log_fields_formats_can_payload() -> None:
    message = SimpleNamespace(arbitration_id=0x18DAF110, data=[0x10, 0x03, 0x22], is_extended_id=True)

    fields = message_to_log_fields(message)

    assert fields == {
        "arbitration_id": 0x18DAF110,
        "arbitration_id_hex": "0x18DAF110",
        "dlc": 3,
        "payload_hex": "10 03 22",
        "is_extended_id": True,
    }


def test_can_formatters_handle_missing_values() -> None:
    assert format_can_id(None) is None
    assert format_payload([]) == ""
