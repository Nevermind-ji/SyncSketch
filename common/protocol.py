import json
import struct


def encode_message(message):
    # Convert dictionary into JSON bytes
    payload = json.dumps(message).encode("utf-8")

    # Create a 4-byte header containing payload length
    header = struct.pack("!I", len(payload))

    return header + payload


def receive_exactly(sock, length):
    data = bytearray()

    while len(data) < length:
        chunk = sock.recv(length - len(data))

        if not chunk:
            return None

        data.extend(chunk)

    return bytes(data)


def receive_message(sock):
    # First receive the 4-byte header
    header = receive_exactly(sock, 4)

    if header is None:
        return None

    # Extract the message length
    length = struct.unpack("!I", header)[0]

    # Receive the complete message
    payload = receive_exactly(sock, length)

    if payload is None:
        return None

    return json.loads(payload.decode("utf-8"))