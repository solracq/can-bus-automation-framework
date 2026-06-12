"""Helpers to create and manage CAN messages."""

from __future__ import annotations

import logging
from typing import Any

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

def send_message(
    bus: can.Bus,
    message: can.Message,
    *,
    log_extra: dict[str, Any] | None = None,
) -> None:
    """Send a CAN message and emit a structured transmit event.

    Args:
        bus: The CAN bus used to send the frame.
        message: The frame to transmit.
        log_extra: Optional structured context appended to the log event.
            This is mainly useful in integration scenarios where we want the
            transmit log to carry domain-specific preconditions such as
            `ignition_status=OFF`, the expected response ID, or the ECU name.
            Adding that context here keeps the CAN transport log and the test
            scenario explanation tied together in the same record.
    """
    log_fields = {"bus": str(bus), **message_to_log_fields(message)}
    # Allow callers to attach scenario context so the raw CAN log still explains
    # why the message was sent under a particular precondition.
    if log_extra:
        log_fields.update(log_extra)
    try:
        logger.info(
            "Sending CAN message",
            extra=build_event_extra("can.tx", **log_fields),
        )
        bus.send(message)
    except Exception as exc:
        logger.error(
            "Error sending CAN message",
            extra=build_event_extra(
                "can.tx.failed",
                error=str(exc),
                **log_fields,
            ),
        )
        raise

def receive_message(
    bus: can.Bus,
    timeout: float = 1.0,
    *,
    log_extra: dict[str, Any] | None = None,
) -> can.Message | None:
    """Receive a CAN message and emit structured receive or timeout events.

    Args:
        bus: The CAN bus used to wait for a frame.
        timeout: Maximum wait time in seconds.
        log_extra: Optional structured context appended to the log event.
            This lets a caller preserve scenario details such as expected
            preconditions or the expected response ID in both successful
            receive logs and timeout logs. That makes failure investigation
            easier because the symptom and the scenario context live together.
    """
    log_fields = {"bus": str(bus), "timeout_s": timeout}
    # Reuse the same scenario metadata on receive-side logs so a timeout can be
    # interpreted without reading the test code first.
    if log_extra:
        log_fields.update(log_extra)
    try:
        received = bus.recv(timeout=timeout)
    except Exception as exc:
        logger.error(
            "Error receiving CAN message",
            extra=build_event_extra("can.rx.failed", error=str(exc), **log_fields),
        )
        raise
    if received is None:
        logger.error(
            "No CAN message received before timeout",
            extra=build_event_extra("can.rx.timeout", **log_fields),
        )
        raise RuntimeError("No message received within timeout.")
    success_fields = {**log_fields, **message_to_log_fields(received)}
    logger.info(
        "Received CAN message",
        extra=build_event_extra("can.rx", **success_fields),
    )
    return received
