# Executing a CAN loopback action

import os
import can

def main() -> int:
    # vcan0 for local virtual CAN tests
    channel = os.getenv("CAN_CHANNEL", "vcan0")
    interface = os.getenv("CAN_INTERFACE", "socketcan")

    print(f"Channel = '{channel}' \nInterface = '{interface}'")

    try:
        # Open a CAN socket on vcan0 using socketCAN
        bus = can.Bus(
            interface=interface,
            channel=channel,
            receive_own_messages=True,  # the same node can recieve the frame it just sent (loopback behaivor)
        )

    except PermissionError as exc:
        print("Couldn't open CAN socket due to permissions")
        print(f"Details: {exc}")
        return 1
    except OSError as exc:
        print(f"Couldn't open CAN interface {channel}, make sure it exists and is UP")
        print(f"Details: {exc}")
        return 1
    
    try:
        # Build one CAN frame
        msg = can.Message(
            arbitration_id=0x123,  # ID= 0x123
            data=[0x11, 0x22, 0x33],  # Data bytes= 11 22 33 (hex)
            is_extended_id=False,  # 11-bit standard ID
        )
        # Transmit frame onto the CAN bus, the frame is published on the bus with arbitration ID 0x123
        bus.send(msg)
        print(f"Send frame on {channel}: {msg}")

        # Wait briefly for loopback traffic and exit cleanly
        received = bus.recv(timeout=1.0)  # Listen for frame
        if received is None:
            print("No frame recieved within 1 secs")
            return 0

        # Confirming bus access works, transmit path works, receive path works, frame formatting is valid
        print(f"Recived: {received}")
        return 0
    finally:
        bus.shutdown()

if __name__ == "__main__":
    raise SystemExit(main())
