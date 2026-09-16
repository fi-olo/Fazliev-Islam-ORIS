import struct

MAX_MESSAGE_SIZE = 10 * 1024 * 1024
HEADER_FORMAT = "!4sI"
HEADER_SIZE = struct.calcsize(HEADER_FORMAT)


def recv_exact(sock, size):
    data = b""
    while len(data) < size:
        chunk = sock.recv(size - len(data))
        if chunk == b"":
            raise ConnectionError("connection closed before all data received")
        data += chunk
    return data


def send_message(sock, command: str, payload: bytes):
    cmd_bytes = command.encode("ascii")
    if len(cmd_bytes) != 4:
        raise ValueError("command must be exactly 4 ASCII characters")
    if len(payload) > MAX_MESSAGE_SIZE:
        raise ValueError("payload too large")
    header = struct.pack(HEADER_FORMAT, cmd_bytes, len(payload))
    sock.sendall(header + payload)


def recv_message(sock):
    try:
        header = recv_exact(sock, HEADER_SIZE)
    except ConnectionError:
        return None
    cmd_bytes, length = struct.unpack(HEADER_FORMAT, header)
    if length > MAX_MESSAGE_SIZE:
        raise ValueError("incoming message too large")
    payload = recv_exact(sock, length) if length else b""
    return cmd_bytes.decode("ascii"), payload