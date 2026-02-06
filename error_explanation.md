# Error Injection Behavior Guide

The behavior you are seeing is correct and demonstrates that the protocol handles **ACK Loss** correctly.

## Scenario 1: Error Config on Receiver (Peer 1) -- RECOMMENDED
Command: `python node.py --error_msg_id 3 ...` on **Peer 1**.
1. **Peer 2** sends Msg 3.
2. **Peer 1** receives Msg 3 -> **Corrupts it** -> Checksum Mismatch -> Drops it.
3. **Peer 2** waiting for ACK -> Timeout -> Retransmits Msg 3.
4. **Peer 1** receives Msg 3 again -> Success.

**Result on Peer 1**: "Checksum Mismatch"
**Result on Peer 2**: "Timeout! Retransmitting"

## Scenario 2: Error Config on Sender (Peer 2) -- YOUR CURRENT TEST
Command: `python node.py --error_msg_id 3 ...` on **Peer 2**.
1. **Peer 2** sends Msg 3.
2. **Peer 1** receives Msg 3 -> **Success** -> Sends ACK 3.
3. **Peer 2** receives ACK 3 -> **Corrupts it** (because it's an incoming packet with SeqNum 3) -> Checksum Mismatch -> Drops ACK.
4. **Peer 2** waiting for valid ACK -> Timeout -> Retransmits Msg 3.
5. **Peer 1** receives Msg 3 **AGAIN** (Duplicate) -> **Success** -> Sends ACK 3.

**Result on Peer 1**: Receives the message TWICE.
**Result on Peer 2**: "Simulating Bit-Flip" (on the ACK) and "Timeout".

## Conclusion
Both scenarios prove the system is reliable!
- **Scenario 1** proves it handles **Corrupt Data**.
- **Scenario 2** proves it handles **Corrupt/Lost ACKs** (by retransmitting).
