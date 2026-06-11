"""Unit tests for the simulated ECU service."""

from __future__ import annotations

import logging
from types import SimpleNamespace

import pytest

from can_framework import simulated_ecu as ecu_module
from can_framework.simulated_ecu import SimulatedECU

pytestmark = pytest.mark.unit


def test_loop_dispatches_registered_handler(caplog: pytest.LogCaptureFixture) -> None:
    handled_ids: list[int] = []
    message = SimpleNamespace(arbitration_id=0x700, data=[0x01], is_extended_id=False)

    def recv(timeout: float):
        assert timeout == 0.1
        ecu.running = False
        return message

    def handler(received_message: object) -> None:
        handled_ids.append(received_message.arbitration_id)

    bus = SimpleNamespace(recv=recv)
    ecu = SimulatedECU(bus=bus, handlers_by_arbitration_id={0x700: handler})
    ecu.running = True
    caplog.set_level(logging.INFO, logger=ecu_module.__name__)

    ecu._loop()

    assert handled_ids == [0x700]
    assert any(record.event_type == "ecu.handler.dispatch" for record in caplog.records)


def test_loop_logs_missing_handler(caplog: pytest.LogCaptureFixture) -> None:
    message = SimpleNamespace(arbitration_id=0x701, data=[0x02], is_extended_id=False)

    def recv(timeout: float):
        ecu.running = False
        return message

    bus = SimpleNamespace(recv=recv)
    ecu = SimulatedECU(bus=bus, handlers_by_arbitration_id={})
    ecu.running = True
    caplog.set_level(logging.WARNING, logger=ecu_module.__name__)

    ecu._loop()

    assert any(record.event_type == "ecu.handler.missing" for record in caplog.records)


def test_loop_logs_handler_failure(caplog: pytest.LogCaptureFixture) -> None:
    message = SimpleNamespace(arbitration_id=0x702, data=[0x03], is_extended_id=False)

    def recv(timeout: float):
        ecu.running = False
        return message

    def handler(received_message: object) -> None:
        _ = received_message
        raise ValueError("bad payload")

    bus = SimpleNamespace(recv=recv)
    ecu = SimulatedECU(bus=bus, handlers_by_arbitration_id={0x702: handler})
    ecu.running = True
    caplog.set_level(logging.ERROR, logger=ecu_module.__name__)

    ecu._loop()

    assert any(record.event_type == "ecu.handler.failed" for record in caplog.records)


def test_start_is_idempotent(monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture) -> None:
    events: list[str] = []

    class FakeThread:
        def __init__(self, target, name: str, daemon: bool) -> None:
            self._target = target
            self._name = name
            self._daemon = daemon

        def start(self) -> None:
            events.append("start")

        def join(self, timeout: float) -> None:
            events.append(f"join:{timeout}")

    monkeypatch.setattr(ecu_module, "can", SimpleNamespace(BusABC=object))
    monkeypatch.setattr(ecu_module.threading, "Thread", FakeThread)
    caplog.set_level(logging.INFO, logger=ecu_module.__name__)

    ecu = SimulatedECU(bus=SimpleNamespace(recv=lambda timeout: None), handlers_by_arbitration_id={})

    ecu.start()
    ecu.start()
    ecu.stop()

    assert events == ["start", "join:1.0"]
    assert any(record.event_type == "ecu.start_skipped" for record in caplog.records)
