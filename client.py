import socket
import sys
import threading
from protocol import send_message, recv_message

HOST = "127.0.0.1"
PORT = 9000


def reader(sock):
    try:
        while True:
            msg = recv_message(sock)
            if msg is None:
                print("\n[client] server closed connection")
                break
            command, payload = msg
            text = payload.decode("utf-8", errors="replace")
            if command == "TEXT":
                print(f"\n{text}")
            elif command == "LIST":
                print(f"\n[users] {text}")
            elif command == "JOIN":
                print(f"\n[server] {text}")
            elif command == "QUIT":
                print(f"\n[server] {text}")
                break
            elif command == "ERRO":
                print(f"\n[error] {text}")
            else:
                print(f"\n[{command}] {text}")
    except ConnectionResetError:
        print("\n[client] connection reset by server")
    except OSError as e:
        print(f"\n[client] socket error: {e}")
    finally:
        try:
            sock.close()
        except OSError:
            pass


def main():
    if len(sys.argv) < 2:
        print("usage: python client.py <username>")
        return
    username = sys.argv[1]

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect((HOST, PORT))
    except OSError as e:
        print(f"[client] cannot connect: {e}")
        return

    try:
        send_message(sock, "JOIN", username.encode("utf-8"))
    except (BrokenPipeError, ConnectionResetError, OSError) as e:
        print(f"[client] failed to join: {e}")
        sock.close()
        return

    t = threading.Thread(target=reader, args=(sock,), daemon=True)
    t.start()

    print("commands: TEXT <msg>, LIST, QUIT")
    try:
        for line in sys.stdin:
            line = line.rstrip("\n")
            if not line:
                continue
            if line == "QUIT":
                try:
                    send_message(sock, "QUIT", b"")
                except (BrokenPipeError, ConnectionResetError, OSError):
                    pass
                break
            elif line == "LIST":
                try:
                    send_message(sock, "LIST", b"")
                except (BrokenPipeError, ConnectionResetError, OSError) as e:
                    print(f"[client] send failed: {e}")
                    break
            elif line.startswith("TEXT "):
                text = line[5:]
                try:
                    send_message(sock, "TEXT", text.encode("utf-8"))
                except (BrokenPipeError, ConnectionResetError, OSError) as e:
                    print(f"[client] send failed: {e}")
                    break
            else:
                print("unknown command; use TEXT <msg>, LIST, QUIT")
    except KeyboardInterrupt:
        pass
    finally:
        try:
            sock.close()
        except OSError:
            pass


if __name__ == "__main__":
    main()