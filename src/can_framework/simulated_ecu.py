"""Simple simulated ECU for SocketCAN/vcan integration tests."""

from __future__ import annotations

import logging
import threading
from dataclasses import dataclass, field
from typing import Callable

from .observability import build_event_extra, message_to_log_fields

try:
    import can  # type: ignore
except ImportError:  # pragma: no cover - optional dependency
    can = None  # type: ignore

logger = logging.getLogger(__name__)

MessageHandler = Callable[["can.Message"], None]


@dataclass(slots=True)
class SimulatedECU:
    """Background receiver loop dispatching CAN messages to handlers."""

    bus: "can.BusABC"
    handlers_by_arbitration_id: dict[int, MessageHandler]
    recv_timeout_s: float = 0.1
    running: bool = field(default=False, init=False)
    _thread: threading.Thread | None = field(default=None, init=False, repr=False)

    def start(self) -> None:
        if can is None:  # pragma: no cover
            raise RuntimeError("python-can is not installed. Install dependencies first.")
        if self.running:
            logger.info("ECU service already running", extra=build_event_extra("ecu.start_skipped"))
            return
        logger.info(
            "Starting ECU service",
            extra=build_event_extra(
                "ecu.start",
                handler_count=len(self.handlers_by_arbitration_id),
                recv_timeout_s=self.recv_timeout_s,
            ),
        )
        self.running = True
        self._thread = threading.Thread(target=self._loop, name="SimulatedECU", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        logger.info("Stopping ECU service", extra=build_event_extra("ecu.stop"))
        self.running = False
        if self._thread is not None:
            self._thread.join(timeout=1.0)
            self._thread = None

    def _loop(self) -> None:
        logger.info("Running ECU service", extra=build_event_extra("ecu.loop.running"))
        while self.running:
            msg = self.bus.recv(timeout=self.recv_timeout_s)
            if msg is None:
                continue

            logger.info(
                "Simulated ECU received CAN message",
                extra=build_event_extra("ecu.rx", **message_to_log_fields(msg)),
            )
            handler = self.handlers_by_arbitration_id.get(msg.arbitration_id)
            if handler is None:
                logger.warning(
                    "No ECU handler registered for message",
                    extra=build_event_extra("ecu.handler.missing", **message_to_log_fields(msg)),
                )
                continue

            try:
                logger.info(
                    "Dispatching ECU handler",
                    extra=build_event_extra("ecu.handler.dispatch", **message_to_log_fields(msg)),
                )
                handler(msg)
            except (RuntimeError, ValueError, OSError):
                logger.exception(
                    "SimulatedECU handler failed",
                    extra=build_event_extra("ecu.handler.failed", **message_to_log_fields(msg)),
                )
