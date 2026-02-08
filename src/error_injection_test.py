import struct

import checksum as cs
from error_injection import inject_error
from packet import Packet


def run_test():
    target_id = 70000
    bit_to_flip = 20  # Bit im 3. Byte (Index 2)

    print("=== Starting Error Injection Test ===")
    print(f"Targeting Message-ID: {target_id} at Bit-Index: {bit_to_flip}")

    # --- 2. create packet ---
    p = (
        Packet()
        .setSenderID("test")
        .setSequenceNumber(target_id)
        .setPayload("Hello Reliability!")
    )

    try:
        valid_bytes = p.to_bytes()
    except struct.error as e:
        print(
            f"Error: Could not pack packet. Check if senderID_length or packetType is still -1! ({e})"
        )
        return

    print(f"Packet created successfully. Checksum in Header: {p.checksum:04x}")

    # --- 3. Initial validation ---
    is_valid_before = cs.validate_checksum(valid_bytes)
    print(f"Is original packet valid? {is_valid_before}")

    # --- 4. Error Injection ---
    corrupted_bytes, debug_msg = inject_error(valid_bytes, bit_to_flip)
    print(f"Injection Result: {debug_msg}")

    # --- 5. validate after error ---
    is_valid_after = cs.validate_checksum(corrupted_bytes)

    print("\n--- Result ---")
    print(f"Is corrupted packet valid? {is_valid_after}")

    if not is_valid_after and is_valid_before:
        print("SUCCESS: 1-bit error was detected. Middleware would drop this message.")
    else:
        print("FAILURE: Error was not detected or original packet was already invalid.")

    # --- 6. binary comparison ---
    byte_idx = bit_to_flip // 8
    print(f"\n--- Binary Debug (Byte {byte_idx}) ---")
    print(f"Original:  {valid_bytes[byte_idx]:08b}")
    print(f"Corrupted: {corrupted_bytes[byte_idx]:08b}")


if __name__ == "__main__":
    run_test()
