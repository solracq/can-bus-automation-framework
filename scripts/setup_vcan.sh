#!/usr/bin/env bash
set -euo pipefail

VCAN_INTERFACE="${VCAN_INTERFACE:-vcan0}"

run_as_root() {
  if [[ "$(id -u)" -eq 0 ]]; then
    "$@"
    return
  fi

  if command -v sudo >/dev/null 2>&1; then
    sudo "$@"
    return
  fi

  echo "Root access is required to configure ${VCAN_INTERFACE}. Re-run as root or install sudo." >&2
  exit 1
}

require_command() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Missing required command: $1" >&2
    exit 1
  fi
}

configure_vcan_with_python() {
  if ! command -v python3 >/dev/null 2>&1; then
    cat >&2 <<EOF
Neither 'ip' nor 'python3' is available to configure '${VCAN_INTERFACE}'.
Install iproute2 on Linux or ensure the container image includes Python dependencies.
EOF
    exit 1
  fi

  run_as_root python3 scripts/setup_vcan.py
}

create_vcan_interface() {
  if ip link show "${VCAN_INTERFACE}" >/dev/null 2>&1; then
    return
  fi

  local first_error=""

  if first_error="$(run_as_root ip link add dev "${VCAN_INTERFACE}" type vcan 2>&1)"; then
    return
  fi

  if command -v modprobe >/dev/null 2>&1; then
    echo "Initial vcan creation failed; attempting to load the vcan kernel module." >&2
    run_as_root modprobe vcan || true

    if run_as_root ip link add dev "${VCAN_INTERFACE}" type vcan; then
      return
    fi
  fi

  cat >&2 <<EOF
Failed to create virtual CAN interface '${VCAN_INTERFACE}'.
Initial error: ${first_error}

Hints:
- Linux host: ensure the kernel provides the vcan driver.
- Docker: run the container with --cap-add=NET_ADMIN.
- If your Docker runtime still reports "Operation not permitted" or "Unknown device type",
  use --privileged or enable vcan in the Linux VM/host kernel.
EOF
  exit 1
}

if command -v ip >/dev/null 2>&1; then
  create_vcan_interface
  run_as_root ip link set up "${VCAN_INTERFACE}"
  ip -details link show "${VCAN_INTERFACE}"
  exit 0
fi

configure_vcan_with_python
