# Exploratory Test Document:

## Purpose
Document to show the initial manual testing activity to understand and validate the product.

## Framework Commands
- `pytest -m "smoke or unit"` : run fast local framework validation
- `./scripts/setup_vcan.sh` : create and bring up the Linux virtual CAN interface
- `RUN_VCAN_TESTS=1 pytest -m integration` : run SocketCAN / vCAN integration tests on Linux
- `python3 tests/integration/simple_example.py` : execute a basic CAN send / receive example
- `./scripts/run_tests_in_docker.sh smoke-unit` : run smoke and unit tests inside Docker
- `./scripts/run_tests_in_docker.sh integration-virtual` : run portable integration tests using python-can virtual backend
- `./scripts/run_tests_in_docker.sh integration` : run true SocketCAN integration inside Docker on Linux
- `docker compose build smoke-unit` : build the smoke / unit Docker workflow
- `docker compose run --rm smoke-unit` : run smoke / unit tests through Docker Compose
- `docker compose build integration-virtual` : build the portable integration Docker workflow
- `docker compose run --rm integration-virtual` : run portable integration tests through Docker Compose

## Notes
- Run commands from the repository root so local imports, Docker build context, and log artifact paths resolve correctly.
- `integration` and `integration-privileged` are intended for real Linux environments with SocketCAN / `vcan` support.
- On macOS or Windows Docker Desktop, use `integration-virtual` instead of true SocketCAN integration.
- When using `zsh`, quote marker expressions such as `pytest -m "smoke or unit"`.

## Terminal Setup
Before running the exploratory scenarios, set the terminal working directory to the root of this repository so pytest, Docker, and helper scripts can resolve correctly.

1. Open a terminal session.
2. Change to the repository root.
3. If using a local Python environment, activate it.
4. Verify commands are executed from the repository root.

Example:
```text
/path/to/can-bus-automation-framework
```

Expected project files and folders:
```text
src/
tests/
scripts/
docs/
Dockerfile
docker-compose.yml
Jenkinsfile
```

## Test Scenarios

### Positive Scenarios
#### Scenario 1: Run local smoke and unit tests
```text
pytest -m "smoke or unit"
```

**Expected**
Smoke and unit tests pass successfully

**Output**
```text
============================= test session starts =============================
tests/smoke/test_framework_smoke.py .
tests/unit/test_validators.py ..

============================== 3 passed in 0.0Xs ==============================
```

#### Scenario 2: Create the Linux virtual CAN interface
**Pre-conditions:**
- Running on Linux or Linux-based environment with SocketCAN / `vcan` support

```text
./scripts/setup_vcan.sh
```

**Expected**
Virtual CAN interface `vcan0` is created and set UP

**Output**
```text
vcan0: <NOARP,UP,LOWER_UP> mtu 16 qdisc noqueue state UNKNOWN mode DEFAULT group default qlen 1000
    link/can
```

#### Scenario 3: Execute the simple CAN example
**Pre-conditions:**
- `vcan0` exists and is UP

```text
python3 tests/integration/simple_example.py
```

**Expected**
A CAN frame is sent and received successfully

**Output**
```text
Channel = 'vcan0'
Interface = 'socketcan'
Send frame on vcan0: Timestamp: ...
Recived: Timestamp: ...
```

#### Scenario 4: Run Linux integration tests with SocketCAN / vCAN
**Pre-conditions:**
- `vcan0` exists and is UP

```text
RUN_VCAN_TESTS=1 pytest -m integration
```

**Expected**
Integration tests pass successfully

**Output**
```text
tests/integration/test_vcan_loopback.py ..
tests/integration/test_simulated_ecu_reaction.py .

============================== 3 passed in 0.XXs ==============================
```

#### Scenario 5: Run smoke and unit tests in Docker
```text
./scripts/run_tests_in_docker.sh smoke-unit
```

**Expected**
Docker image builds and smoke / unit tests pass

**Output**
```text
...
3 passed, 3 deselected in 0.XXs
```

#### Scenario 6: Run portable integration tests in Docker
```text
./scripts/run_tests_in_docker.sh integration-virtual
```

**Expected**
Portable integration tests pass using the `virtual` backend

**Output**
```text
...
3 passed, 3 deselected in 0.XXs
```

#### Scenario 7: Run smoke and unit tests with Docker Compose
```text
docker compose build smoke-unit
docker compose run --rm smoke-unit
```

**Expected**
Docker Compose builds the image and smoke / unit tests pass

**Output**
```text
...
3 passed, 3 deselected in 0.XXs
```

#### Scenario 8: Run portable integration tests with Docker Compose
```text
docker compose build integration-virtual
docker compose run --rm integration-virtual
```

**Expected**
Docker Compose runs the portable integration workflow successfully

**Output**
```text
...
3 passed, 3 deselected in 0.XXs
```

### Negative Scenarios
#### Scenario 9: Run integration tests without enabling `RUN_VCAN_TESTS`
```text
pytest -m integration
```

**Expected**
Integration tests are skipped because they are opt-in

**Output**
```text
SKIPPED [1] Set RUN_VCAN_TESTS=1 to run vcan integration tests.
```

#### Scenario 10: Run Linux integration tests without `vcan0`
**Pre-conditions:**
- Linux environment without `vcan0` configured

```text
RUN_VCAN_TESTS=1 pytest -m integration
```

**Expected**
Integration test setup fails or skips because the CAN interface is unavailable

**Output**
```text
SKIPPED [1] socketcan vcan0 not available/up: [Errno ...]
```

#### Scenario 11: Run real SocketCAN integration on macOS Docker Desktop
```text
./scripts/run_tests_in_docker.sh integration
```

**Expected**
Execution is rejected with a clear message indicating that true `vcan` support requires Linux

**Output**
```text
SocketCAN/vcan integration requires a Linux kernel with vcan support.
Docker Desktop on Darwin typically does not expose the vcan link type, even with --privileged.
```

#### Scenario 12: Run Docker Compose with unsupported `--build` flag on older Compose versions
```text
docker compose run --build --rm smoke-unit
```

**Expected**
Older Compose versions may reject the flag

**Output**
```text
unknown flag: --build
```

#### Scenario 13: Validate assertion failure for incorrect message timing
```text
pytest tests/unit/test_validators.py::test_assert_message_period_fails_outside_tolerance -q
```

**Expected**
The test passes because the framework correctly raises an assertion for out-of-tolerance timing

**Output**
```text
1 passed in 0.0Xs
```

### Edge Scenarios
#### Scenario 14: Run portable integration tests repeatedly to confirm stable repeatability
```text
./scripts/run_tests_in_docker.sh integration-virtual
./scripts/run_tests_in_docker.sh integration-virtual
```

**Expected**
The same tests pass repeatedly without environment drift

**Output**
```text
...
3 passed, 3 deselected in 0.XXs
...
3 passed, 3 deselected in 0.XXs
```

#### Scenario 15: Generate framework log files during a pytest run
```text
PYTEST_LOG_FILE=exploratory-run.log pytest -m "smoke or unit"
```

**Expected**
The run passes and a log file is written under `log/`

**Output**
```text
============================== 3 passed in 0.0Xs ==============================
```

```text
log/exploratory-run.log
```

#### Scenario 16: Validate Docker-based smoke tests after cleaning previous artifacts
```text
rm -rf artifacts
./scripts/run_tests_in_docker.sh smoke-unit
```

**Expected**
A clean Docker-based run still succeeds

**Output**
```text
...
3 passed, 3 deselected in 0.XXs
```

### Integration Scenarios
#### Scenario 17: Run full Docker smoke and portable integration workflow
```text
./scripts/run_tests_in_docker.sh all
```

**Expected**
Smoke / unit tests and portable integration tests run successfully on non-Linux systems

**Output**
```text
...
3 passed, 3 deselected in 0.XXs
...
3 passed, 3 deselected in 0.XXs
```

#### Scenario 18: Run the Linux Docker integration workflow with SocketCAN
**Pre-conditions:**
- Real Linux environment with `vcan` support

```text
./scripts/run_tests_in_docker.sh integration
```

**Expected**
True SocketCAN integration tests pass inside Docker

**Output**
```text
...
3 passed in 0.XXs
```

#### Scenario 19: Run the Linux Docker integration workflow with privileged mode if needed
**Pre-conditions:**
- Real Linux environment
- `NET_ADMIN` alone is not sufficient

```text
INTEGRATION_CONTAINER_MODE=privileged ./scripts/run_tests_in_docker.sh integration
```

**Expected**
Integration tests pass when broader container privileges are required

**Output**
```text
...
3 passed in 0.XXs
```

#### Scenario 20: Validate Jenkins-oriented artifact generation through local Docker execution
```text
mkdir -p artifacts/junit artifacts/logs
docker run --rm \
  -v "$PWD/artifacts:/artifacts" \
  -e PYTEST_LOG_DIR=/artifacts/logs \
  -e PYTEST_LOG_FILE=smoke-unit.log \
  can-bus-automation-framework-tests:local \
  pytest -q -m "smoke or unit" --junitxml=/artifacts/junit/smoke-unit.xml
```

**Expected**
JUnit XML and log files are generated in the mounted `artifacts/` directory

**Output**
```text
...
3 passed, 3 deselected in 0.XXs
```

```text
artifacts/junit/smoke-unit.xml
artifacts/logs/smoke-unit.log
```
