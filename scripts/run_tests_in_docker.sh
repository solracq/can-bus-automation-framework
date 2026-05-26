#!/usr/bin/env bash
set -euo pipefail

IMAGE_NAME="${IMAGE_NAME:-can-bus-automation-framework-tests:local}"
CAN_CHANNEL="${CAN_CHANNEL:-vcan0}"
CAN_INTERFACE="${CAN_INTERFACE:-socketcan}"
INTEGRATION_CONTAINER_MODE="${INTEGRATION_CONTAINER_MODE:-net-admin}"
FORCE_SOCKETCAN_IN_DOCKER="${FORCE_SOCKETCAN_IN_DOCKER:-0}"
MODE="${1:-all}"
shift || true

require_command() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Missing required command: $1" >&2
    exit 1
  fi
}

build_image() {
  docker build -t "${IMAGE_NAME}" .
}

host_os() {
  uname -s
}

require_linux_for_socketcan() {
  if [[ "${FORCE_SOCKETCAN_IN_DOCKER}" == "1" ]]; then
    return
  fi

  if [[ "$(host_os)" == "Linux" ]]; then
    return
  fi

  cat >&2 <<EOF
SocketCAN/vcan integration requires a Linux kernel with vcan support.
Docker Desktop on $(host_os) typically does not expose the vcan link type, even with --privileged.

Use one of these instead:
- ./scripts/run_tests_in_docker.sh integration-virtual
- docker compose run --build --rm integration-virtual
- a real Linux host or Linux-based Jenkins agent for ./scripts/run_tests_in_docker.sh integration

If you have a custom non-Linux runtime that really does expose vcan, re-run with FORCE_SOCKETCAN_IN_DOCKER=1.
EOF
  exit 1
}

run_smoke_and_unit() {
  docker run --rm "${IMAGE_NAME}" pytest -q -m "smoke or unit" "$@"
}

run_integration() {
  local integration_flags=()

  require_linux_for_socketcan

  case "${INTEGRATION_CONTAINER_MODE}" in
    net-admin)
      integration_flags=(--cap-add=NET_ADMIN)
      ;;
    privileged)
      integration_flags=(--privileged)
      ;;
    *)
      echo "Unsupported INTEGRATION_CONTAINER_MODE: ${INTEGRATION_CONTAINER_MODE}" >&2
      echo "Use net-admin or privileged." >&2
      exit 1
      ;;
  esac

  docker run --rm \
    "${integration_flags[@]}" \
    -e RUN_VCAN_TESTS=1 \
    -e CAN_CHANNEL="${CAN_CHANNEL}" \
    -e CAN_INTERFACE="${CAN_INTERFACE}" \
    "${IMAGE_NAME}" \
    pytest -q -m integration "$@"
}

run_virtual_integration() {
  docker run --rm \
    -e RUN_VCAN_TESTS=1 \
    -e CAN_CHANNEL="${CAN_CHANNEL}" \
    -e CAN_INTERFACE=virtual \
    "${IMAGE_NAME}" \
    pytest -q -m integration "$@"
}

require_command docker

if [[ "${MODE}" == "integration" && "${CAN_INTERFACE}" == "socketcan" ]]; then
  require_linux_for_socketcan
fi

build_image

case "${MODE}" in
  smoke-unit)
    run_smoke_and_unit "$@"
    ;;
  integration)
    run_integration "$@"
    ;;
  integration-virtual)
    run_virtual_integration "$@"
    ;;
  all)
    run_smoke_and_unit "$@"
    if [[ "${CAN_INTERFACE}" == "socketcan" && "$(host_os)" == "Linux" ]]; then
      run_integration "$@"
    else
      run_virtual_integration "$@"
    fi
    ;;
  *)
    echo "Unknown mode: ${MODE}" >&2
    echo "Usage: $0 [smoke-unit|integration|integration-virtual|all] [extra pytest args...]" >&2
    exit 1
    ;;
esac
