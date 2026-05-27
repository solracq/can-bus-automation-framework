# Test Plan:

## 1. Test Objectives
The objective of this testing is to verify and validate that the CAN bus automation framework works as expected and meets the defined business and technical requirements.

Since the focus of the testing will be on the validation of CAN message communication behaviour and the interaction with the framework utilities, the testing will involve framework-level checks, local virtual CAN execution, and containerized test execution. Thus, the QA team will validate specifically the functional behaviour, the reliability, the portability, and the maintainability of the automation framework product.

## 2. Entry, Suspension, and Exit Criteria
This section defines the criteria for starting, suspending, and completing the test cycle.

### 2.1 Entry Criteria
- Python dependencies are installed.
- Smoke tests can be executed locally.
- For SocketCAN integration tests, the virtual CAN interface is available on Linux or the Docker-based Linux environment is ready.
- Required environment variables are configured when integration tests are executed.
- Test data and reusable CAN scenarios are available.

### 2.2 Suspension Criteria
- If 40% or more of the test cases fail.
- The framework cannot open the configured CAN interface.
- Docker-based test execution is unavailable when required for the selected test scope.
- Test environment configuration is invalid or incomplete.

### 2.3 Exit Criteria
- If 98% of all test cases pass.
- All critical and high-severity defects are resolved or accepted.
- Smoke and regression tests pass.
- Test results are documented.

## 3. Test Resources
The validation of the feature will require the following resources:
* One SDET
* Python
* Pytest
* python-can
* cantools
* SocketCAN / vCAN
* Docker
* Jenkins
* Linux environment for real SocketCAN / vCAN integration validation

## 4. Test Environment
The installation of the software will require the following:
* MacOS or Linux
* Python 3
* Linux virtual CAN support for real SocketCAN integration tests
* Docker for containerized execution
* Jenkins for CI-based execution and report publication
* Python modules:
    - pytest
    - python-can
    - cantools
    - pyroute2

## 5. Scope

### In Scope
- Validation of CAN message ID checks.
- Validation of CAN message timing behaviour.
- SocketCAN / vCAN loopback workflows.
- Simulated ECU response workflows.
- Docker-based test execution for portability.
- Jenkins CI execution and test report publication.

### Out of Scope
- Testing with physical CAN hardware devices.
- Vehicle-level end-to-end validation with real ECUs.
- OEM-specific network databases or proprietary CAN stacks.
- Frontend/UI testing.

## 6. Test Coverage
- Unit tests for framework utilities
- Smoke tests for framework readiness
- Integration tests for SocketCAN / vCAN loopback and simulated ECU workflows
- Containerized test execution for local portability and CI repeatability

### Test Scenarios
tests/unit/
  test_validators.py

tests/smoke/
  test_framework_smoke.py

tests/integration/
  test_vcan_loopback.py
  test_simulated_ecu_reaction.py

### Test Data
The test suite will use:
- Valid CAN arbitration IDs
- Invalid or unexpected CAN arbitration IDs
- Timestamp sequences within tolerance
- Timestamp sequences outside tolerance
- Virtual CAN channel names such as `vcan0`
- Simulated request and response CAN frames
- Missing or unavailable CAN interfaces for integration setup validation

### Defect Management
Defects will be documented using GitHub Issues. Each defect should include:
- Summary
- Steps to reproduce
- Expected result
- Actual result
- Severity
- Logs or screenshots, if applicable

## 9. Schedule & Estimates
This project is planned as a personal automation framework. Test design, implementation, and execution will be completed iteratively as framework features are added.

Estimated phases:
- Phase 1: Environment setup and smoke tests
- Phase 2: Core validation utility and CAN workflow tests
- Phase 3: Integration execution with SocketCAN / vCAN and simulated ECU scenarios
- Phase 4: Docker, Jenkins CI execution, regression runs, and documentation

## 10. Test Deliverables
* Before testing:
    * Test plan
    * Test strategy
    * README about details of the local, Docker, and Jenkins execution setup
* During testing:
    * Test cases
    * Automated tests
    * Automation framework
    * Logs
    * Bug reports
* After testing:
    * Test Results
    * Release notes
