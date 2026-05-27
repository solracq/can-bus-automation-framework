import os

import pytest

from can_framework.bus import close_bus, open_bus
from can_framework.simulated_ecu import SimulatedECU

pytestmark = pytest.mark.integration

CAN_CHANNEL = os.getenv("CAN_CHANNEL", "vcan0")
CAN_INTERFACE = os.getenv("CAN_INTERFACE", "socketcan")


def test_simulated_ecu_reacts_to_request() -> None:
    """Kernel-level integration test: send request, assert ECU response."""
    if os.getenv("RUN_VCAN_TESTS") != "1":
        pytest.skip("Set RUN_VCAN_TESTS=1 to run vcan integration tests.")

    can = pytest.importorskip("can")

    try:
        tester_bus = open_bus(channel=CAN_CHANNEL, interface=CAN_INTERFACE)
        ecu_bus = open_bus(channel=CAN_CHANNEL, interface=CAN_INTERFACE)
    except OSError as exc:
        pytest.skip(f"{CAN_INTERFACE} {CAN_CHANNEL} not available/up: {exc}")

    REQ_ID = 0x700
    RESP_ID = 0x701

    def on_request(msg: can.Message) -> None:
        # Simple “reaction”: if first byte is 0x01, respond with 0x02.
        if len(msg.data) >= 1 and msg.data[0] == 0x01:
            ecu_bus.send(
                can.Message(
                    arbitration_id=RESP_ID,
                    data=[0x02],
                    is_extended_id=False,
                )
            )

    ecu: SimulatedECU | None = None

    try:
        request = can.Message(arbitration_id=REQ_ID, data=[0x01], is_extended_id=False)

        if CAN_INTERFACE == "virtual":
            # The portable virtual backend is used on non-Linux hosts; keep the
            # ECU emulation synchronous so this fallback does not depend on
            # background thread creation inside the container runtime.
            tester_bus.send(request)
            incoming = ecu_bus.recv(timeout=1.0)
            assert incoming is not None, "No request received by the simulated ECU."
            on_request(incoming)
        else:
            ecu = SimulatedECU(bus=ecu_bus, handlers_by_arbitration_id={REQ_ID: on_request})
            ecu.start()
            tester_bus.send(request)

        received = tester_bus.recv(timeout=1.0)
        assert received is not None, "No ECU response received within 1 second."
        assert received.arbitration_id == RESP_ID
        assert list(received.data) == [0x02]
    finally:
        if ecu is not None:
            ecu.stop()
        close_bus(tester_bus)
        close_bus(ecu_bus)
