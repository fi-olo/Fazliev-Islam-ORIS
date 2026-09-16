import socket
import threading
from protocol import send_message, recv_message

HOST = "0.0.0.0"
PORT = 9000

clients = {}
clients_lock = threading.Lock()


def broadcast(command, payload, exclude=None):
    with clients_lock:
        targets = [(s, u) for s, u in clients.items() if s is not exclude]
    for sock, _ in targets:
        try:
            send_message(sock, command, payload)
        except (BrokenPipeError, ConnectionResetError, OSError):
            pass


def remove_client(sock):
    with clients_lock:
        username = clients.pop(sock, None)
    return username


def handle_client(sock, addr):
    username = None
    try:
        msg = recv_message(sock)
        if msg is None:
            return
        command, payload = msg
        if command != "JOIN":
            send_message(sock, "ERRO", b"first command must be JOIN")
            return
        username = payload.decode("utf-8", errors="replace").strip()
        if not username:
            send_message(sock, "ERRO", b"empty username")
            return
        with clients_lock:
            if any(u == username for u in clients.values()):
                send_message(sock, "ERRO", b"username already taken")
                return
            clients[sock] = username
        print(f"[server] {username} joined from {addr}")
        broadcast("JOIN", f"{username} joined the chat".encode("utf-8"), exclude=sock)

        while True:
            msg = recv_message(sock)
            if msg is None:
                print(f"[server] {username} disconnected (recv returned None)")
                break
            command, payload = msg
            if command == "TEXT":
                text = payload.decode("utf-8", errors="replace")
                broadcast("TEXT", f"{username}: {text}".encode("utf-8"), exclude=sock)
            elif command == "LIST":
                with clients_lock:
                    names = ", ".join(sorted(clients.values()))
                send_message(sock, "LIST", names.encode("utf-8"))
            elif command == "QUIT":
                send_message(sock, "QUIT", b"bye")
                print(f"[server] {username} quit")
                break
            else:
                send_message(sock, "ERRO", f"unknown command: {command}".encode("utf-8"))
    except ConnectionResetError:
        print(f"[server] {addr} connection reset")
    except BrokenPipeError:
        print(f"[server] {addr} broken pipe")
    except OSError as e:
        print(f"[server] {addr} socket error: {e}")
    finally:
        removed = remove_client(sock)
        if removed:
            print(f"[server] {removed} removed")
            broadcast("JOIN", f"{removed} left the chat".encode("utf-8"))
        try:
            sock.close()
        except OSError:
            pass


def main():
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_sock.bind((HOST, PORT))
    server_sock.listen()
    print(f"[server] listening on {HOST}:{PORT}")
    try:
        while True:
            try:
                client_sock, addr = server_sock.accept()
            except OSError as e:
                print(f"[server] accept error: {e}")
                continue
            t = threading.Thread(target=handle_client, args=(client_sock, addr), daemon=True)
            t.start()
    except KeyboardInterrupt:
        print("[server] shutting down")
    finally:
        server_sock.close()


if __name__ == "__main__":
    main()