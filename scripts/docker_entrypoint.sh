#!/usr/bin/env bash
# Prepares runtime-only CAN setup before executing the requested test command.
set -euo pipefail

if [[ "${RUN_VCAN_TESTS:-0}" == "1" && "${CAN_INTERFACE:-socketcan}" == "socketcan" ]]; then
  export VCAN_INTERFACE="${VCAN_INTERFACE:-${CAN_CHANNEL:-vcan0}}"
  ./scripts/setup_vcan.sh
fi

if [[ "$#" -eq 0 ]]; then
  set -- pytest -q
fi

exec "$@"
