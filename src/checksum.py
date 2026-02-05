def internet_checksum(data: bytes) -> int:
    """
    Calculates the 16-bit one's complement sum of the input data as defined in RFC 1071.

    This function processes the data in 16-bit words. If the data length is odd,
    a zero padding byte is appended. It handles carries by adding them back
    to the least significant bit (end-around carry).

    Args:
        data: The byte array to calculate the checksum for.

    Returns:
        int: The 16-bit inverted one's complement sum.
    """
    if len(data) % 2 == 1:
        data += b"\x00"

    total_sum = 0
    for i in range(0, len(data), 2):
        word = (data[i] << 8) + data[i + 1]
        total_sum += word
        while total_sum >> 16:
            total_sum = (total_sum & 0xFFFF) + (total_sum >> 16)

    return (~total_sum) & 0xFFFF


def validate_checksum(raw_data: bytes) -> bool:
    """
    Validates the integrity of a received packet using the RFC 1071 algorithm.

    The function calculates the checksum over the entire packet (header including
    the received checksum, and payload). Due to the properties of one's complement
    arithmetic, a valid packet must result in a checksum of zero.

    Args:
        raw_data: The complete received packet as bytes.

    Returns:
        bool: True if the checksum is valid (result is 0), False otherwise.
    """

    if len(raw_data) < 8:
        return False

    # 1. Die empfangene Checksumme aus dem Header extrahieren (Index 5 & 6)
    received_checksum = (raw_data[5] << 8) + raw_data[6]

    # 2. Eine Kopie der Daten erstellen, bei der die Checksumme 0 ist
    mutable_data = bytearray(raw_data)
    mutable_data[5] = 0
    mutable_data[6] = 0

    # 3. Checksumme neu berechnen
    recalculated = internet_checksum(bytes(mutable_data))

    # 4. Vergleichen
    return received_checksum == recalculated
