"""Helpers to create and manage CAN messages."""

from __future__ import annotations

import logging

from .observability import build_event_extra, message_to_log_fields

try:
    import can  # type: ignore
except ImportError:  # pragma: no cover - optional dependency
    can = None  # type: ignore

logger = logging.getLogger(__name__)


def create_message(arbitration_id: int, data: list[int], is_extended_id: bool = False) -> can.Message:
    """Create a CAN message."""
    try:
        message = can.Message(
            arbitration_id=arbitration_id,
            data=data,
            is_extended_id=is_extended_id,
        )
        logger.info(
            "Created CAN message",
            extra=build_event_extra("can.message.created", **message_to_log_fields(message)),
        )
        return message
    except Exception as exc:
        logger.error(
            "Error creating CAN message",
            extra=build_event_extra(
                "can.message.create_failed",
                arbitration_id=arbitration_id,
                data=data,
                is_extended_id=is_extended_id,
                error=str(exc),
            ),
        )
        raise

def send_message(bus: can.Bus, message: can.Message) -> None:
    """Send a CAN message."""
    try:
        logger.info(
            "Sending CAN message",
            extra=build_event_extra("can.tx", bus=str(bus), **message_to_log_fields(message)),
        )
        bus.send(message)
    except Exception as exc:
        logger.error(
            "Error sending CAN message",
            extra=build_event_extra(
                "can.tx.failed",
                bus=str(bus),
                error=str(exc),
                **message_to_log_fields(message),
            ),
        )
        raise

def receive_message(bus: can.Bus, timeout: float = 1.0) -> can.Message | None:
    """Receive a CAN message."""
    try:
        received = bus.recv(timeout=timeout)
    except Exception as exc:
        logger.error(
            "Error receiving CAN message",
            extra=build_event_extra("can.rx.failed", bus=str(bus), timeout_s=timeout, error=str(exc)),
        )
        raise
    if received is None:
        logger.error(
            "No CAN message received before timeout",
            extra=build_event_extra("can.rx.timeout", bus=str(bus), timeout_s=timeout),
        )
        raise RuntimeError("No message received within timeout.")
    logger.info(
        "Received CAN message",
        extra=build_event_extra("can.rx", bus=str(bus), timeout_s=timeout, **message_to_log_fields(received)),
    )
    return received
