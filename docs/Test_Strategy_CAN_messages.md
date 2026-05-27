# Test Strategy:

## 1. Purpose
This test strategy defines the overall testing approach for the CAN Bus Automation Framework. It explains the scope, test levels, test types, environments, risks, tools, and quality practices used to validate CAN message communication workflows, local virtual CAN execution, and CI-based test execution.

## 2. Test Scope
Validation will focus on interactions with the software through the CAN framework utilities and the CAN communication interface. Therefore, the scope of this testing is to validate the framework logic, the CAN communication behaviour, and the backend execution flow of the product.

Since the focus of this CAN communication validation is on the automation framework and backend execution, the validation of the User Interface of the software is out of scope.

#### What this validates
- CAN arbitration ID validation
- Message timing validation
- SocketCAN / vCAN loopback communication
- Simulated ECU request / response behaviour
- Docker-based execution for local portability
- Jenkins CI-based execution and report publication
- Negative cases: unavailable CAN interface, missing vCAN setup, invalid timing, unexpected message IDs
- Retry and execution behaviour when integration environments are unavailable
- Audit / log validation from framework logs and CI artifacts

## 3. System Specifications
For the system under test, we won't be using physical CAN hardware as the primary validation environment. Instead, part of this project is to validate CAN communication through a Python-based framework using virtual CAN interfaces and containerized Linux execution when needed.

#### System under test
- CAN Bus Automation Framework implemented in Python
- SocketCAN / vCAN-based local or containerized CAN execution
- Simulated ECU helper for request / response validation
- python-can framework layer for CAN interaction
- Docker-based execution path for repeatable local and CI test runs
- Jenkins pipeline for automated test execution and report publication

## 4. Roles
The development and QA roles are responsible for implementation, validation, and test automation.
Carlos Quiroz - Software Developer Engineer in Test

## 5. Test Levels
- Unit Testing: Validates framework utilities and validation helpers.
- Smoke Testing: Confirms the framework imports and core assertions are ready.
- Integration Testing: Validates SocketCAN / vCAN loopback behaviour and simulated ECU workflows.
- Negative Testing: Validates expected failures for unavailable interfaces, invalid timing, and unexpected message conditions.
- Regression Testing: Re-runs core scenarios after framework, Docker, or Jenkins changes.

## 6. Testing Types
The following testing types will be used to verify and validate the product.
- Functional Testing
- Reliability Testing
- Regression Testing
- Configuration / Environment Testing
- CI Report Publication Testing

## 7. Risk Analysis
* Risk 1: SocketCAN / vCAN support depends on the host or containerized Linux kernel configuration.
    * Occurrence : Medium
    * Severity: High
    * Mitigation: Use Linux environments for true SocketCAN testing and document `integration-virtual` as the portable fallback for non-Linux systems.
* Risk 2: Docker Desktop on non-Linux hosts may not expose the `vcan` link type.
    * Occurrence : High
    * Severity: Medium
    * Mitigation: Use the portable virtual backend locally and reserve true SocketCAN validation for Linux hosts or Linux Jenkins agents.
* Risk 3: Jenkins or Docker configuration changes may break report publication or automated execution.
    * Occurrence : Medium
    * Severity: Medium
    * Mitigation: Keep Jenkins pipeline definitions version-controlled and validate archived XML and log artifacts as part of regression runs.
* Risk 4: Invalid local environment setup may cause false failures for integration scenarios.
    * Occurrence : Medium
    * Severity: Medium
    * Mitigation: Provide clear setup instructions, default Docker execution paths, and explicit environment checks before running integration tests.

## 8. Automation Strategy
Automated tests will be written in Python using Pytest. Tests will be grouped by purpose:
- `tests/unit/`
- `tests/smoke/`
- `tests/integration/`

Reusable CAN operations and validation helpers will be implemented in framework modules to avoid duplication and improve maintainability.

## 9. CI/CD Strategy
The project can be integrated with Jenkins to run Docker-based automated tests on commits or pipeline executions. For local and CI dependency execution, Docker will be used to provide a repeatable test environment, while Linux Jenkins agents can execute true SocketCAN / vCAN integration scenarios and publish XML and log artifacts.

## 10. Test Logistics
The validation of the product in matter will be performed by one SDET on the next sprint after feature is completed. So, it is required that the test requirements, Linux or virtual CAN execution environment, Docker setup, Jenkins pipeline, and SDET to be available in order to start testing.
