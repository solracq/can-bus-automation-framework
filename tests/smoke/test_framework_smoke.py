"""Smoke tests for the framework. Test the assert_message_id function."""

import logging
import pytest

from can_framework import assert_message_id

logger = logging.getLogger(__name__)

pytestmark = pytest.mark.smoke

class DummyMessage:
    def __init__(self, arbitration_id: int):
        self.arbitration_id = arbitration_id


def test_import_and_basic_assertion() -> None:
    message = DummyMessage(arbitration_id=0x100)
    logger.debug("Dummy message=%s", message)
    assert_message_id(message, expected_id=0x100)
