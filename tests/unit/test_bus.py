"""Unit tests for CAN bus helpers."""

from __future__ import annotations

import logging
from types import SimpleNamespace

import pytest

from can_framework import bus as bus_module

pytestmark = pytest.mark.unit


def test_open_bus_passes_expected_parameters(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}
    sentinel = object()

    def fake_bus(**kwargs: object) -> object:
        captured.update(kwargs)
        return sentinel

    monkeypatch.setattr(bus_module, "can", SimpleNamespace(Bus=fake_bus))

    bus = bus_module.open_bus(channel="virtual0", interface="virtual", receive_own_messages=True)

    assert bus is sentinel
    assert captured == {
        "interface": "virtual",
        "channel": "virtual0",
        "receive_own_messages": True,
    }


def test_open_bus_raises_when_python_can_is_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(bus_module, "can", None)

    with pytest.raises(RuntimeError, match="python-can is not installed"):
        bus_module.open_bus()


def test_close_bus_shuts_down_bus(caplog: pytest.LogCaptureFixture) -> None:
    shutdown_called = False

    class FakeBus:
        def shutdown(self) -> None:
            nonlocal shutdown_called
            shutdown_called = True

    caplog.set_level(logging.INFO, logger=bus_module.__name__)

    bus_module.close_bus(FakeBus())

    assert shutdown_called is True
    assert any(record.event_type == "can.bus.closed" for record in caplog.records)


def test_close_bus_wraps_shutdown_errors(caplog: pytest.LogCaptureFixture) -> None:
    class FakeBus:
        def shutdown(self) -> None:
            raise OSError("driver busy")

    caplog.set_level(logging.ERROR, logger=bus_module.__name__)

    with pytest.raises(RuntimeError, match="driver busy"):
        bus_module.close_bus(FakeBus())

    assert any(record.event_type == "can.bus.close_failed" for record in caplog.records)
