import os

import pytest

from can_framework.bus import close_bus, open_bus
from can_framework.message import receive_message, send_message

pytestmark = pytest.mark.integration

CAN_CHANNEL = os.getenv("CAN_CHANNEL", "vcan0")
CAN_INTERFACE = os.getenv("CAN_INTERFACE", "socketcan")


def test_open_vcan_bus() -> None:
    """Opt-in integration test for local vcan setup."""
    if os.getenv("RUN_VCAN_TESTS") != "1":
        pytest.skip("Set RUN_VCAN_TESTS=1 to run vcan integration tests.")

    # Import can module through pytest.importorskip() only if RUN_VCAN_TESTS is set to 1
    can = pytest.importorskip("can")

    # Open a CAN bus on vcan0 using socketCAN
    try:
        bus = open_bus(
            channel=CAN_CHANNEL, 
            interface=CAN_INTERFACE)
    except OSError as exc:
        pytest.skip(f"{CAN_INTERFACE} {CAN_CHANNEL} not available/up: {exc}")
    try:
        assert isinstance(bus, can.BusABC)
    finally:
        close_bus(bus)


def test_send_and_receive_message() -> None:
    """Opt-in integration test for sending and receiving a message on a CAN bus."""
    if os.getenv("RUN_VCAN_TESTS") != "1":
        pytest.skip("Set RUN_VCAN_TESTS=1 to run vcan integration tests.")

    # Import can module through pytest.importorskip() only if RUN_VCAN_TESTS is set to 1
    can = pytest.importorskip("can")

    # Open a CAN bus on vcan0 using socketCAN
    try:
        bus = open_bus(
            channel=CAN_CHANNEL,
            interface=CAN_INTERFACE,
            receive_own_messages=True,
        )
    except OSError as exc:
        pytest.skip(f"{CAN_INTERFACE} {CAN_CHANNEL} not available/up: {exc}")
    assert bus is not None
    try:
        msg = can.Message(
            arbitration_id=0x123,
            data=[0x11, 0x22, 0x33],
            is_extended_id=False,
        )

        send_message(bus, msg)
        received = receive_message(bus, timeout=1.0)
        assert received is not None, "No frame received within 1 second."

        assert received.arbitration_id == msg.arbitration_id
        assert list(received.data) == list(msg.data)
    finally:
        close_bus(bus)
