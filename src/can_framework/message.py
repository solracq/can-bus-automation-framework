"""Helpers to create and manage CAN messages."""

from __future__ import annotations

import logging

try:
    import can  # type: ignore
except ImportError:  # pragma: no cover - optional dependency
    can = None  # type: ignore

logger = logging.getLogger(__name__)


def create_message(arbitration_id: int, data: list[int], is_extended_id: bool = False) -> can.Message:
    """Create a CAN message."""
    return can.Message(
        arbitration_id=arbitration_id,
        data=data,
        is_extended_id=is_extended_id,
    )

def send_message(bus: can.Bus, message: can.Message) -> None:
    """Send a CAN message."""
    logger.info(f"Sending message: {message}")
    try:
        bus.send(message)
    except Exception as e:
        logger.error(f"Error sending message: {e}")
        raise e

def receive_message(bus: can.Bus, timeout: float = 1.0) -> can.Message | None:
    """Receive a CAN message."""
    received = bus.recv(timeout=timeout)
    if received is None:
        raise RuntimeError("No message received within timeout.")
    return received