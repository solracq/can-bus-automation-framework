"""Unit tests for CAN message helpers."""

from __future__ import annotations

import logging
from types import SimpleNamespace

import pytest

from can_framework import message as message_module

pytestmark = pytest.mark.unit


class FakeMessage:
    def __init__(self, arbitration_id: int, data: list[int], is_extended_id: bool) -> None:
        self.arbitration_id = arbitration_id
        self.data = data
        self.is_extended_id = is_extended_id


def test_create_message_returns_can_message(monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture) -> None:
    monkeypatch.setattr(message_module, "can", SimpleNamespace(Message=FakeMessage, Bus=object))
    caplog.set_level(logging.INFO, logger=message_module.__name__)

    message = message_module.create_message(0x123, [0x11, 0x22, 0x33], is_extended_id=False)

    assert message.arbitration_id == 0x123
    assert message.data == [0x11, 0x22, 0x33]
    created_event = next(record for record in caplog.records if record.event_type == "can.message.created")
    assert created_event.arbitration_id_hex == "0x123"
    assert created_event.payload_hex == "11 22 33"


def test_send_message_uses_bus_and_logs_event(caplog: pytest.LogCaptureFixture) -> None:
    sent_messages: list[FakeMessage] = []

    class FakeBus:
        def send(self, message: FakeMessage) -> None:
            sent_messages.append(message)

    message = FakeMessage(arbitration_id=0x222, data=[0xAA], is_extended_id=False)
    caplog.set_level(logging.INFO, logger=message_module.__name__)

    message_module.send_message(FakeBus(), message)

    assert sent_messages == [message]
    assert any(record.event_type == "can.tx" for record in caplog.records)


def test_receive_message_returns_received_frame(caplog: pytest.LogCaptureFixture) -> None:
    message = FakeMessage(arbitration_id=0x456, data=[0x99, 0x01], is_extended_id=False)

    class FakeBus:
        def recv(self, timeout: float) -> FakeMessage:
            assert timeout == 0.5
            return message

    caplog.set_level(logging.INFO, logger=message_module.__name__)

    received = message_module.receive_message(FakeBus(), timeout=0.5)

    assert received is message
    assert any(record.event_type == "can.rx" for record in caplog.records)


def test_receive_message_raises_on_timeout(caplog: pytest.LogCaptureFixture) -> None:
    class FakeBus:
        def recv(self, timeout: float) -> None:
            assert timeout == 1.25
            return None

    caplog.set_level(logging.ERROR, logger=message_module.__name__)

    with pytest.raises(RuntimeError, match="No message received within timeout"):
        message_module.receive_message(FakeBus(), timeout=1.25)

    timeout_event = next(record for record in caplog.records if record.event_type == "can.rx.timeout")
    assert timeout_event.timeout_s == 1.25
