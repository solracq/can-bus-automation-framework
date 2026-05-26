import os

import pytest

from can_framework.bus import close_bus, open_bus
from can_framework.simulated_ecu import SimulatedECU

pytestmark = pytest.mark.integration

def test_simulated_ecu_reacts_to_request() -> None:
    """Kernel-level integration test: send request, assert ECU response."""
    if os.getenv("RUN_VCAN_TESTS") != "1":
        pytest.skip("Set RUN_VCAN_TESTS=1 to run vcan integration tests.")

    can = pytest.importorskip("can")

    try:
        tester_bus = open_bus(channel="vcan0", interface="socketcan")
        ecu_bus = open_bus(channel="vcan0", interface="socketcan")
    except OSError as exc:
        pytest.skip(f"SocketCAN vcan0 not available/up: {exc}")

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

    ecu = SimulatedECU(bus=ecu_bus, handlers_by_arbitration_id={REQ_ID: on_request})
    ecu.start()
    try:
        tester_bus.send(
            can.Message(arbitration_id=REQ_ID, data=[0x01], is_extended_id=False)
        )

        received = tester_bus.recv(timeout=1.0)
        assert received is not None, "No ECU response received within 1 second."
        assert received.arbitration_id == RESP_ID
        assert list(received.data) == [0x02]
    finally:
        ecu.stop()
        close_bus(tester_bus)
        close_bus(ecu_bus)
