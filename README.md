# can-bus-automation-framework
Automation framework for validating CAN (Controller Area Network) bus message flows and controller-level communication scenarios.

A Controller Area Network (CAN) is the nervous system inside vehicles. Every ECU (Electronic Control Unit)—brake module, infotainment, etc.—broadcasts short messages over a shared bus.
Testing CAN messages means verifying that message communication is correct, reliable, and safe.

CAN messages contain:
- ID (message priority)
- Data payload
- Timing (how often it appears)

CAN testing goals:
- What is sent
- When it is sent
- How systems react

Functional correctness:
- Does the right message ID appear?
- Are the signal values encoded/decoded correctly?
- Do ECUs react correctly to received messages?

Python tools:
- python-can (CAN interaction in Python)
- cantools (decoding/encoding CAN messages based on DBC files)
- pytest
- SocketCAN on Linux for kernel-level integration tests
- Simulated ECU or message responder

Checking that the virtual CAN interface is working on Linux:
1) Confirm the interface exists and is up
   ip -details link show vcan0  -> Look for "state UP" and "link/can"
2) Confirm CAN type    ->  Look for "vcan" / CAN-specific details
   ip -d link show vcan0
3) Live traffic check (sudo apt install can-utils)
   candump vcan0
4) In another terminal, send a test frame:
   cansend vcan0 123#DEADBEEF  -> first terminal: vcan0  123   [4]  DE AD BE EF
If "vcan0" is missing, run: ./scripts/setup_vcan.sh

Simulated ECU Helper:
For kernel-level tests (SocketCAN + vcan0), a mock ECU helper is implemented as a simulated ECU process/thread that listens/responds on vcan0. This helper consists of the following:
- opens its own SocketCAN bus on vcan0
- recv() requests
- applies a small state machine / handler
- send() response frames
This SocketCAN setup uses the kernel CAN stack to test real timing/loopback/routing behavior while still controlling ECU logic deterministically in Python.

## Folder structure

```text
can-bus-automation-framework/
├── .dockerignore
├── Dockerfile
├── Jenkinsfile
├── configs/
│   └── test_environment.example.json
├── dbc/
├── docs/
│   └── STEP_BY_STEP.md
├── scripts/
│   ├── docker_entrypoint.sh
│   ├── run_tests_in_docker.sh
│   ├── setup_vcan.py
│   └── setup_vcan.sh
├── src/
│   └── can_framework/
│       ├── __init__.py
│       ├── bus.py
│       ├── message.py
│       ├── simulated_ecu.py
│       └── validators.py
├── tests/
│   ├── conftest.py
│   ├── integration/
│   │   ├── simple_example.py
│   │   ├── test_vcan_loopback.py
│   │   └── test_simulated_ecu_reaction.py
│   ├── smoke/
│   │   └── test_framework_smoke.py
│   └── unit/
│       └── test_validators.py
├── pytest.ini
└── requirements.txt
```

## Quick start

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Run smoke/unit tests:

```bash
pytest -m "smoke or unit"
```

3. Run SocketCAN integration tests natively on Linux:

```bash
./scripts/setup_vcan.sh
RUN_VCAN_TESTS=1 pytest -m integration
```

4. Run the same test flows through Docker on any machine (e.g. macOS) with Docker, where tests are run directly on the host OS. For faster setup and easier to debug:

```bash
./scripts/run_tests_in_docker.sh smoke-unit
./scripts/run_tests_in_docker.sh integration
./scripts/run_tests_in_docker.sh integration-virtual
./scripts/run_tests_in_docker.sh all
```

5. Run the same flows with Docker Compose, where Docker runs the tests inside the repo's container image. For consistency, portability, and CI-like execution. :

```bash
docker compose build smoke-unit
docker compose run --rm smoke-unit

docker compose build integration-virtual
docker compose run --rm integration-virtual

docker compose build integration
docker compose run --rm integration

docker compose build integration-privileged
docker compose run --rm integration-privileged
```

**Note on docker compose execution**
- Use `integration-virtual` on macOS/Docker Desktop
- Use `integration` on a real Linux host or Linux Jenkins agent

6. Run the integration tests on real Linux machine or a Linux Jenkins agent. For real SocketCAN/vcan integration, where real Linux host or Linux Jenkins agent are needed:

```bash
./scripts/run_tests_in_docker.sh integration
```

If NET_ADMIN is not enough on that machine, try:
```bash
INTEGRATION_CONTAINER_MODE=privileged ./scripts/run_tests_in_docker.sh integration
```

**Note:**
During development run the following:
```bash
pytest -m "smoke or unit"
```
or
```bash
docker compose build smoke-unit
docker compose run --rm smoke-unit
```

## Docker test workflow

The Docker image provides a Linux userspace with `python-can` and a Python-based `vcan0` setup helper via `pyroute2`.
This makes smoke/unit tests portable across macOS, Windows, and Linux, and it gives integration tests the same runtime shape used by CI.

- `scripts/run_tests_in_docker.sh smoke-unit` runs fast tests without extra container privileges.
- `scripts/run_tests_in_docker.sh integration` runs the true `SocketCAN` tests in a Linux container with `--cap-add=NET_ADMIN`.
- `scripts/run_tests_in_docker.sh integration-virtual` runs the same integration test files against `python-can`'s portable `virtual` backend.
- `docker compose build ...` followed by `docker compose run --rm ...` is the most version-compatible Compose flow.
- The `socketcan` integration runner exports `RUN_VCAN_TESTS=1` and provisions `vcan0` inside the container before `pytest` starts.

**Note:**
* `--cap-add=NET_ADMIN`: is a Docker runtime permission. It gives the container network admin capabilities.
* `RUN_VCAN_TESTS=1`: is an env variable flag. It means "yes, run the opt-in CAN integration tests". Without this flag, integration tests are skipped and `vcan0` setup is not attempted.

Why this changed:
- Some Docker Desktop environments fail while unpacking Debian packages during `apt-get install iproute2`.
- The container no longer needs `apt` for `vcan` setup, which avoids that class of build failure entirely.

Run split approach:
- Local macOS/Windows development: `smoke-unit` plus `integration-virtual`
- Linux or Linux-based Jenkins agent: `integration` for true `SocketCAN/vcan`

If you are on Docker Desktop for macOS and see:
- `unknown flag: --build`
  use `docker compose build <service>` first, then `docker compose run --rm <service>`
- `Failed to create 'vcan0': (95, 'Operation not supported')`
  that means Docker Desktop's Linux VM does not expose the `vcan` link type, even with `privileged: true`
  use `integration-virtual` locally, and reserve `integration` / `integration-privileged` for real Linux hosts or Linux Jenkins agents

If Docker runtime reports `Operation not permitted` or `Unknown device type` while creating `vcan0`, the Linux kernel behind Docker does not currently expose `vcan`. In that case:

- switch to `integration-virtual` for local non-Linux development, or
- retry the integration container with `INTEGRATION_CONTAINER_MODE=privileged ./scripts/run_tests_in_docker.sh integration`, or
- enable the `vcan` module on the Linux host or Docker Desktop VM, or
- run the integration stage on a Linux Jenkins agent.

## Jenkins

The included `Jenkinsfile` builds the same Docker test image and runs:

1. smoke and unit tests
2. SocketCAN integration tests with `--cap-add=NET_ADMIN`

That gives local Docker runs and Jenkins the same execution path, which is the key part for portability and repeatability.

## AI Assistance Disclosure

Parts of this project were developed with AI assistance (OpenAI Codex/LLM tools) for scaffolding, code suggestions, and documentation drafting.
All generated content was reviewed, tested, and validated by the project maintainer before commit/merge.
