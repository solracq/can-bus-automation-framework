"""Assertion helpers specialized for CAN message validation."""

from __future__ import annotations


def assert_message_id(message, expected_id: int) -> None:
    """
    Assert CAN arbitration ID. Validate the arbitration ID of a CAN message.
    Args:
        message: The CAN message to validate.
        expected_id: The expected arbitration ID.
    """
    actual_id = getattr(message, "arbitration_id", None)
    assert actual_id == expected_id, (
        f"Unexpected message ID. Expected=0x{expected_id:X}, got={actual_id!r}"
    )


def assert_message_period(
    timestamps: list[float], expected_period_s: float, tolerance_s: float = 0.01
) -> None:
    """
    Assert that each interval is within tolerance around the expected period.
    Args:
        timestamps: The list of timestamps to validate.
        expected_period_s: The expected period in seconds.
        tolerance_s: The tolerance in seconds.
    """
    assert len(timestamps) >= 2, "Need at least 2 timestamps to check message timing."

    intervals = [
        timestamps[index + 1] - timestamps[index]
        for index in range(len(timestamps) - 1)
    ]

    for interval in intervals:
        delta = abs(interval - expected_period_s)
        assert delta <= tolerance_s, (
            f"Interval {interval:.6f}s is outside tolerance. "
            f"Expected {expected_period_s:.6f}s +/- {tolerance_s:.6f}s"
        )
