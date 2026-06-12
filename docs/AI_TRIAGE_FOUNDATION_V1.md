# AI Triage Foundation V1

This document captures the first design decisions for an AI-assisted CAN test failure triage tool.

The goal is not to replace the SDET or test automator. The goal is to help testers:

- summarize failures faster
- detect likely bug patterns earlier
- preserve strong evidence while investigating
- suggest focused next steps

This is a design document, not an implementation document.

## Scope

This V1 foundation covers:

- the failure taxonomy
- the first triage report schema
- the distinction between classification labels and raw evidence

This V1 does not yet define:

- a concrete LLM prompt
- a specific local model choice
- an agent workflow
- automatic code fixing

## Design Principles

The triage tool should be:

- human-centered
  It should help testers reason faster, not hide evidence behind a black box.

- evidence-first
  Classifications should be traceable back to logs, assertions, and known scenario context.

- layered
  One failure should not be forced into a single flat label if multiple perspectives matter.

- conservative
  The tool should be allowed to say `unknown` or use low confidence.

- local-model friendly
  The schema should work whether the reasoning engine is rules-only, a local LLM, or a hybrid system.

## Why Use 5 Fields Instead Of One Label

A single flat label is usually not enough for test failure triage.

Example:

- the test symptom may be `no_response_timeout`
- the likely cause may be `precondition_not_met`
- the likely layer may be `ecu_application`
- the likely first owner may be `shared_investigation`

These are not the same kind of information.

For that reason, V1 uses 5 classification fields:

- `symptom`
- `likely_cause`
- `layer`
- `owner_hint`
- `confidence`

## Timeout Modeling Rule

`timeout` should be modeled in two places:

- as part of the symptom label:
  `symptom = no_response_timeout`
- as raw evidence:
  `evidence.timeout_s = 0.5`

Why:

- plain `timeout` is too broad as a taxonomy label
- the numeric value like `0.5` seconds is evidence, not a class name
- `no_response_timeout` is more actionable than `timeout`

## V1 Taxonomy

### Field Table

| Field | Meaning | Allowed Values | Why It Exists |
|---|---|---|---|
| `symptom` | What the test directly observed | `no_response_timeout`, `unexpected_response_id`, `payload_mismatch`, `timing_violation`, `bus_or_interface_failure`, `other_assertion_failure`, `unknown_symptom` | Gives the tester-facing shape of the failure |
| `likely_cause` | Best diagnosis hypothesis from the available evidence | `precondition_not_met`, `ecu_silent`, `routing_or_mapping_error`, `encoding_decoding_error`, `timing_regression`, `test_harness_issue`, `environment_issue`, `unknown_cause` | Explains why the failure likely happened |
| `layer` | Where the problem most likely lives | `ecu_application`, `gateway_routing`, `can_transport`, `signal_encoding`, `test_harness`, `execution_environment`, `unknown_layer` | Helps route the investigation |
| `owner_hint` | Who should probably look first | `product_team`, `test_automation`, `platform_infra`, `shared_investigation` | Helps triage workflow |
| `confidence` | Strength of the evidence supporting the classification | `high`, `medium`, `low` | Prevents overclaiming |

### Field Definitions And Examples

| Field | Value | Definition | Example |
|---|---|---|---|
| `symptom` | `no_response_timeout` | Request was sent, but no response arrived before the timeout | `can.tx` followed by `can.rx.timeout` |
| `symptom` | `unexpected_response_id` | A response arrived, but on the wrong CAN ID | `can.rx` followed by `validator.message_id_failed` |
| `symptom` | `payload_mismatch` | A response arrived, but its bytes or decoded signals are wrong | future payload validator case |
| `symptom` | `timing_violation` | The right behavior happened outside timing tolerance | `validator.message_period_failed` |
| `symptom` | `bus_or_interface_failure` | The test could not communicate because the interface or runtime was not available | interface unavailable, dependency missing |
| `symptom` | `other_assertion_failure` | The test failed, but not through a known CAN-specific bucket yet | generic assertion failure |
| `likely_cause` | `precondition_not_met` | A required state, mode, or session was missing | `ecu.response.suppressed` with `ignition_status=OFF` |
| `likely_cause` | `ecu_silent` | The ECU did not answer and no stronger explanation was found | timeout with no earlier cause clue |
| `likely_cause` | `routing_or_mapping_error` | Message routing, gateway logic, or response ID mapping is wrong | wrong response ID scenario |
| `likely_cause` | `encoding_decoding_error` | Signal encoding, payload composition, or decode logic is wrong | future payload mismatch case |
| `likely_cause` | `timing_regression` | Timing behavior drifted beyond tolerance | timing validator failure |
| `likely_cause` | `test_harness_issue` | Failure likely comes from the test code, fixture, or expectation | fixture setup bug |
| `likely_cause` | `environment_issue` | Failure likely comes from tooling or runtime setup | missing dependency, interface not up |
| `layer` | `ecu_application` | ECU business logic, session logic, or internal behavior | silent ECU due to wrong precondition |
| `layer` | `gateway_routing` | Gateway forwarding or response mapping logic | response arrived on wrong CAN ID |
| `layer` | `can_transport` | Lower transport behavior, delivery, or bus access | transport-level communication issue |
| `layer` | `signal_encoding` | Raw bytes or signals are encoded or interpreted incorrectly | payload mismatch case |
| `layer` | `test_harness` | Test code, fixture, setup, or expectation logic | bad expected value |
| `layer` | `execution_environment` | Host, container, virtual bus, CI agent, or dependency layer | environment failure |

### Current Scenario Mapping

| Scenario | symptom | likely_cause | layer | owner_hint | confidence |
|---|---|---|---|---|---|
| Ignition precondition missing | `no_response_timeout` | `precondition_not_met` | `ecu_application` | `shared_investigation` | `high` |
| Unexpected response ID | `unexpected_response_id` | `routing_or_mapping_error` | `gateway_routing` | `product_team` | `high` |

## Triage Report Schema V1

The taxonomy answers only part of the problem.

The full triage output should include:

- metadata
- classification
- evidence
- narrative explanation
- next actions

### Design Goals For The Report

The report should be:

- easy for a tester to read in under one minute
- structured enough for later automation
- compatible with rules, local LLMs, or a hybrid approach

### Report Sections

| Section | Purpose |
|---|---|
| `report_metadata` | Identifies the report, schema version, run, and test |
| `classification` | Stores the 5 finalized taxonomy fields |
| `evidence` | Preserves the facts used to support the classification |
| `narrative` | Gives a concise explanation in natural language |
| `next_actions` | Suggests concrete follow-up steps |
| `fix_hints` | Optional possible repair ideas, clearly marked as suggestions |

### Report Schema Table

| Field | Required | Description | Example |
|---|---|---|---|
| `schema_version` | yes | Version of the triage report contract | `1.0` |
| `report_id` | yes | Unique report identifier | `triage-20260612-001` |
| `run_id` | yes | Test session identifier from the logs | `learning-timeout-20260611` |
| `test_name` | yes | Full pytest node id | `tests/integration/test_failure_scenarios.py::test_gateway_times_out_when_ignition_precondition_is_missing` |
| `status` | yes | Overall test result | `failed` |
| `symptom` | yes | Final taxonomy value | `no_response_timeout` |
| `likely_cause` | yes | Final taxonomy value | `precondition_not_met` |
| `layer` | yes | Final taxonomy value | `ecu_application` |
| `owner_hint` | yes | Final taxonomy value | `shared_investigation` |
| `confidence` | yes | Final taxonomy value | `high` |
| `summary` | yes | One or two sentence human-readable failure summary | `The request was transmitted on 0x700, the ECU observed it, but no response arrived before 0.5s because ignition was OFF.` |
| `key_events` | yes | Ordered list of the most relevant event types and short notes | `scenario.failure.started`, `can.tx`, `ecu.response.suppressed`, `can.rx.timeout`, `pytest.test.failed` |
| `key_fields` | yes | Important structured evidence values | `request_id_hex`, `expected_response_id_hex`, `payload_hex`, `timeout_s`, `precondition` |
| `timeline_excerpt` | no | Small ordered subset of log lines or event objects | selected JSON events |
| `suspected_component` | no | Optional component or ECU name | `CentralGateway` |
| `suspected_network` | no | Optional network hint | `BodyCAN` |
| `root_cause_rationale` | yes | Why the classification was chosen | explanation linked to earlier evidence |
| `next_actions` | yes | Short list of recommended checks | verify ignition precondition, compare session setup, inspect gateway rules |
| `possible_fix_hints` | no | Optional suggestions, not authoritative fixes | ensure ignition/session setup before request |
| `open_questions` | no | What is still uncertain | was the precondition intentional or a product bug |

## Example V1 Report

```json
{
  "schema_version": "1.0",
  "report_id": "triage-20260612-001",
  "run_id": "learning-timeout-20260611",
  "test_name": "tests/integration/test_failure_scenarios.py::test_gateway_times_out_when_ignition_precondition_is_missing",
  "status": "failed",
  "symptom": "no_response_timeout",
  "likely_cause": "precondition_not_met",
  "layer": "ecu_application",
  "owner_hint": "shared_investigation",
  "confidence": "high",
  "summary": "The request on 0x700 was transmitted successfully, the ECU observed it, but no response arrived before 0.5 seconds because the ignition precondition was not met.",
  "key_events": [
    "scenario.failure.started",
    "can.tx",
    "ecu.response.suppressed",
    "can.rx.timeout",
    "pytest.test.failed"
  ],
  "key_fields": {
    "ecu_name": "CentralGateway",
    "network": "BodyCAN",
    "request_id_hex": "0x700",
    "expected_response_id_hex": "0x708",
    "precondition": "ignition_status=OFF",
    "timeout_s": 0.5
  },
  "suspected_component": "CentralGateway",
  "suspected_network": "BodyCAN",
  "root_cause_rationale": "The log shows the request was sent, the ECU-side scenario explicitly recorded that the response was suppressed due to ignition_status=OFF, and the tester then timed out waiting for the expected response.",
  "next_actions": [
    "Verify whether ignition OFF is expected in this test setup.",
    "Check whether the ECU specification requires ignition ON before 0x700 requests.",
    "Compare with a passing run where the same request produced 0x708."
  ],
  "possible_fix_hints": [
    "Set the required ignition or session precondition before sending the request."
  ],
  "open_questions": [
    "Is the missing precondition intentional test coverage or an unexpected product regression?"
  ]
}
```

## Evidence Rules

The report should clearly separate:

- classification
- evidence
- suggestion

This is important because the tool should not present a guess as if it were a proven fact.

Recommended rule:

- values such as `timeout_s`, `payload_hex`, `request_id_hex`, and `actual_response_id_hex` belong in evidence
- values such as `no_response_timeout` or `routing_or_mapping_error` belong in classification
- values such as `check gateway response ID mapping` belong in next actions or fix hints

## Recommended V1 Workflow

Before introducing an LLM, the workflow can already be:

1. collect structured log events
2. extract the key event chain
3. classify across the 5 taxonomy fields
4. build a V1 report using the schema above

Later, a local LLM can improve:

- the summary
- the rationale
- the next actions
- the possible fix hints

without changing the taxonomy or report contract.

## Next Design Step

The next logical design step after this document is:

- compare a rules-only triage pipeline versus a hybrid rules + local LLM pipeline using this exact taxonomy and report schema
