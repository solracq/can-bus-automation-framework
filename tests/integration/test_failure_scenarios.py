"""Opt-in failing integration scenarios used to study structured logs."""

from __future__ import annotations

import logging
import os

import pytest

from can_framework.bus import close_bus, open_bus
from can_framework.message import receive_message, send_message
from can_framework.observability import build_event_extra, format_can_id

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.integration, pytest.mark.failure_scenario]

CAN_CHANNEL = os.getenv("CAN_CHANNEL", "vcan0")
CAN_INTERFACE = os.getenv("CAN_INTERFACE", "socketcan")


def test_gateway_times_out_when_ignition_precondition_is_missing() -> None:
    """Intentional failure: request is observed, but the ECU suppresses the response."""
    if os.getenv("RUN_VCAN_TESTS") != "1":
        pytest.skip("Set RUN_VCAN_TESTS=1 to run vcan integration tests.")
    if os.getenv("RUN_FAILURE_SCENARIOS") != "1":
        pytest.skip("Set RUN_FAILURE_SCENARIOS=1 to run intentional failure scenarios.")

    can = pytest.importorskip("can")

    try:
        tester_bus = open_bus(channel=CAN_CHANNEL, interface=CAN_INTERFACE)
        ecu_bus = open_bus(channel=CAN_CHANNEL, interface=CAN_INTERFACE)
    except OSError as exc:
        pytest.skip(f"{CAN_INTERFACE} {CAN_CHANNEL} not available/up: {exc}")

    req_id = 0x700
    resp_id = 0x708
    scenario_log_extra = {
        "scenario": "ignition_precondition_missing",
        "ecu_name": "CentralGateway",
        "network": "BodyCAN",
        "request_id_hex": format_can_id(req_id),
        "expected_response_id_hex": format_can_id(resp_id),
        "precondition": "ignition_status=OFF",
    }

    try:
        request = can.Message(
            arbitration_id=req_id,
            data=[0x02, 0x10, 0x03],
            is_extended_id=False,
        )

        logger.info(
            "Starting intentional timeout scenario",
            extra=build_event_extra(
                "scenario.failure.started",
                **scenario_log_extra,
            ),
        )
        send_message(tester_bus, request, log_extra=scenario_log_extra)

        incoming = ecu_bus.recv(timeout=1.0)
        assert incoming is not None, "The simulated ECU never observed the diagnostic request."
        logger.warning(
            "ECU suppressed the expected response because ignition is off",
            extra=build_event_extra(
                "ecu.response.suppressed",
                observed_request_id_hex=format_can_id(incoming.arbitration_id),
                observed_payload_hex=" ".join(f"{byte:02X}" for byte in incoming.data),
                **scenario_log_extra,
            ),
        )

        receive_message(tester_bus, timeout=0.5, log_extra=scenario_log_extra)
    finally:
        close_bus(tester_bus)
        close_bus(ecu_bus)
