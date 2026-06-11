"""Helpers to open and manage a CAN bus connection."""

from __future__ import annotations

import logging
from typing import Any

from .observability import build_event_extra

try:
    import can  # type: ignore
except ImportError:  # pragma: no cover - optional dependency
    can = None  # type: ignore

logger = logging.getLogger(__name__)


def open_bus(channel: str = "vcan0", interface: str = "socketcan", receive_own_messages: bool = False):
    """Open a CAN bus using python-can.

    Raises:
        RuntimeError: If python-can is not installed.
    """
    if can is None:  # pragma: no cover - import guard
        raise RuntimeError("python-can is not installed. Install dependencies first.")

    logger.info(
        "Opening CAN bus",
        extra=build_event_extra(
            "can.bus.open",
            bus_channel=channel,
            can_interface=interface,
            receive_own_messages=receive_own_messages,
        ),
    )
    return can.Bus(
        interface=interface,
        channel=channel,
        receive_own_messages=receive_own_messages,
    )

def close_bus(bus: Any) -> None:
    """Close a CAN bus."""
    logger.info("Closing CAN bus", extra=build_event_extra("can.bus.close", bus=str(bus)))
    try:
        bus.shutdown()
        logger.info("Closed CAN bus", extra=build_event_extra("can.bus.closed", bus=str(bus)))
    except Exception as exc:
        logger.error(
            "Error closing CAN bus",
            extra=build_event_extra("can.bus.close_failed", bus=str(bus), error=str(exc)),
        )
        raise RuntimeError(f"Error closing CAN bus: {exc}")
