"""Helpers to open and manage a CAN bus connection."""

from __future__ import annotations

try:
    import can  # type: ignore
except ImportError:  # pragma: no cover - optional dependency
    can = None  # type: ignore


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
