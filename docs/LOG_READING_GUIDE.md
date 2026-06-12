# Log Reading Guide

This project emits structured CAN test logs so a failure can be read as a short timeline instead of a single assertion error.

## How to read a failing scenario

Look for the events in this order:

1. `scenario.failure.started`
   This is the scenario breadcrumb. It tells you the business context such as:
   - `scenario`
   - `ecu_name`
   - `network`
   - `precondition`
   - `request_id_hex`
   - `expected_response_id_hex`

2. `can.tx`
   This confirms the tester sent the request frame.
   Useful fields:
   - `arbitration_id_hex`
   - `payload_hex`
   - `bus_channel`

3. ECU-side warning event
   This explains what the simulated ECU decided to do.
   Current examples:
   - `ecu.response.suppressed`
   - `ecu.response.unexpected_id`

4. Receive-side result
   This shows the tester-side symptom:
   - `can.rx` means a response arrived
   - `can.rx.timeout` means nothing arrived before the timeout

5. Validator failure
   If the frame arrived but is wrong, expect a validator event such as:
   - `validator.message_id_failed`
   - `validator.message_period_failed`

6. `pytest.test.failed`
   This is the final pytest outcome for the test phase.

## Symptom vs cause

Try to separate these two:

- Symptom:
  What the tester observed, such as `can.rx.timeout` or `validator.message_id_failed`
- Cause:
  What earlier event explains it, such as `ecu.response.suppressed`

Example:

- `can.rx.timeout` says the response never came back
- `ecu.response.suppressed` says why it never came back

## Most useful fields

These fields usually matter first:

- `event_type`: what kind of event happened
- `test_name`: which test was running
- `run_id`: which test session the event belongs to
- `ecu_name`: which ECU the scenario is about
- `request_id_hex`: request CAN ID
- `expected_response_id_hex`: response we wanted
- `actual_response_id_hex`: response we actually got, when relevant
- `payload_hex`: raw message bytes in hex
- `precondition`: scenario condition such as `ignition_status=OFF`
- `timeout_s`: how long the test waited

## Quick diagnosis patterns

- `can.tx` + `can.rx.timeout`
  The request left the tester, but no response came back.

- `can.tx` + `ecu.response.suppressed` + `can.rx.timeout`
  The ECU observed the request and intentionally stayed silent because a precondition was not met.

- `can.tx` + `can.rx` + `validator.message_id_failed`
  A response arrived, but it came back on the wrong CAN ID.
