"""Helpers to open and manage a CAN bus connection."""

from __future__ import annotations

import logging
from typing import Any

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

    return can.Bus(
        interface=interface,
        channel=channel,
        receive_own_messages=receive_own_messages,
    )

def close_bus(bus: Any) -> None:
    """Close a CAN bus."""
    try:
        bus.shutdown()
        logger.info(f"Closed CAN bus: {bus}")
    except Exception as exc:
        logger.error(f"Error closing CAN bus: {exc}")
        raise