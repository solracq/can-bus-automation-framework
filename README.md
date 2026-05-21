# can-bus-automation-framework
Simple automation framework to validate Controller Area Network (CAN) messages.

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
- SocketCAN (creates a virtual CAN interface)
     - sudo modprobe vcan
     - sudo ip link add dev vcan0 type vcan
     - sudo ip link set up vcan0
- Simulated ECU or message responder

Checking that the virtual CAN interface is working:
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

## Initial folder structure

```text
can-bus-automation-framework/
├── configs/
│   └── test_environment.example.json
├── dbc/
├── docs/
│   └── STEP_BY_STEP.md
├── scripts/
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
pytest
```

3. (Optional) Set up virtual CAN for integration tests:

```bash
./scripts/setup_vcan.sh
RUN_VCAN_TESTS=1 pytest -m integration
```

4. Run integration tests:

```bash
RUN_VCAN_TESTS=1 python3 -m pytest -q tests/integration/test_vcan_loopback.py
RUN_VCAN_TESTS=1 python3 -m pytest -q tests/integration/test_simulated_ecu_reaction.py
```

## AI Assistance Disclosure

Parts of this project were developed with AI assistance (OpenAI Codex/LLM tools) for scaffolding, code suggestions, and documentation drafting.
All generated content was reviewed, tested, and validated by the project maintainer before commit/merge.
