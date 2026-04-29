"""Unit tests for the validators module. Test the assert_message_period function."""

import pytest

from can_framework.validators import assert_message_period


def test_assert_message_period_passes_within_tolerance() -> None:
    timestamps = [0.0, 0.100, 0.201, 0.301]
    assert_message_period(timestamps, expected_period_s=0.1, tolerance_s=0.01)


def test_assert_message_period_fails_outside_tolerance() -> None:
    timestamps = [0.0, 0.100, 0.250]

    with pytest.raises(AssertionError):
        assert_message_period(timestamps, expected_period_s=0.1, tolerance_s=0.01)
