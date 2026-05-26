#!/usr/bin/env python3
"""Configure a virtual CAN interface without relying on iproute2 binaries."""

from __future__ import annotations

import os
import sys

from pyroute2 import IPRoute
from pyroute2.netlink.exceptions import NetlinkError


VCAN_INTERFACE = os.getenv("VCAN_INTERFACE", "vcan0")


def _interface_index(ipr: IPRoute, name: str) -> int | None:
    matches = ipr.link_lookup(ifname=name)
    return matches[0] if matches else None


def main() -> int:
    try:
        with IPRoute() as ipr:
            interface_index = _interface_index(ipr, VCAN_INTERFACE)

            if interface_index is None:
                try:
                    ipr.link("add", ifname=VCAN_INTERFACE, kind="vcan")
                except NetlinkError as exc:
                    if exc.code != 17:
                        raise RuntimeError(
                            f"Failed to create '{VCAN_INTERFACE}': {exc}"
                        ) from exc

                interface_index = _interface_index(ipr, VCAN_INTERFACE)
                if interface_index is None:
                    raise RuntimeError(
                        f"Created '{VCAN_INTERFACE}' but could not look it up afterwards."
                    )

            ipr.link("set", index=interface_index, state="up")
    except NetlinkError as exc:
        print(
            f"Failed to configure '{VCAN_INTERFACE}' via netlink: {exc}",
            file=sys.stderr,
        )
        print(
            "Hint: run the container with --cap-add=NET_ADMIN or --privileged, "
            "and ensure the Linux kernel exposes the vcan driver.",
            file=sys.stderr,
        )
        return 1
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    print(f"Configured virtual CAN interface '{VCAN_INTERFACE}' and set it UP.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
