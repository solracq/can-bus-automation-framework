"""Simple simulated ECU for SocketCAN/vcan integration tests."""

from __future__ import annotations

import logging
import threading
from dataclasses import dataclass, field
from typing import Callable

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
            return
        self.running = True
        self._thread = threading.Thread(target=self._loop, name="SimulatedECU", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self.running = False
        if self._thread is not None:
            self._thread.join(timeout=1.0)
            self._thread = None

    def _loop(self) -> None:
        while self.running:
            msg = self.bus.recv(timeout=self.recv_timeout_s)
            if msg is None:
                continue

            handler = self.handlers_by_arbitration_id.get(msg.arbitration_id)
            if handler is None:
                continue

            try:
                handler(msg)
            except (RuntimeError, ValueError, OSError):
                logger.exception("SimulatedECU handler failed")
