import socket
import threading
import protocol as proto

HOST = "0.0.0.0"
PORT = 5555

tasks = []
tasks_lock = threading.Lock()

clients = {}
clients_lock = threading.Lock()


def format_tasks():
    with tasks_lock:
        if not tasks:
            return "To-do list empty"
        lines = []
        for i, t in enumerate(tasks, start=1):
            mark = "x" if t["done"] else " "
            lines.append(f"{i}. [{mark}] {t['text']}")
        return "\n".join(lines)


def handle_command(line):
    parts = line.strip().split(maxsplit=1)
    if not parts:
        return "Empty command. Available: /add, /list, /done, /delete, /quit"

    cmd = parts[0].lower()
    arg = parts[1] if len(parts) > 1 else ""

    if cmd == "/list":
        return format_tasks()

    if cmd == "/add":
        text = arg.strip()
        if not text:
            return "Error: use /add <task>"
        with tasks_lock:
            tasks.append({"text": text, "done": False})
            number = len(tasks)
        return f"Task added: {number}. [ ] {text}"

    if cmd == "/done":
        if not arg.isdigit():
            return "Error: use /done <number of task>"
        number = int(arg)
        with tasks_lock:
            if 1 <= number <= len(tasks):
                tasks[number - 1]["done"] = True
                return f"Task {number} mark as completed."
            return f"Error: task with number {number} dont exist."

    if cmd == "/delete":
        if not arg.isdigit():
            return "Error: use /delete <number of task>"
        number = int(arg)
        with tasks_lock:
            if 1 <= number <= len(tasks):
                removed = tasks.pop(number - 1)
                return f"Task removed: {removed['text']}"
            return f"Error: task with number {number} dont exist."

    return f"Unknown command: {cmd}. Avalable: /add, /list, /done, /delete, /quit"


def handle_client(sock, addr):
    username = f"{addr[0]}:{addr[1]}"
    try:
        with clients_lock:
            clients[sock] = username
        print(f"+ Connected {username}")

        proto.send_message(
            sock,
            "TEXT",
            ("Welcome to to-do!\n"
             "Command: /add <text>, /list, /done <number>, /delete <number>, /quit").encode()
        )

        while True:
            try:
                msg = proto.recv_message(sock)
            except (ConnectionResetError, BrokenPipeError, OSError) as e:
                print(f"[server] {username} socket error: {e}")
                msg = None

            if msg is None:
                print(f"[i] {username} left without /quit")
                break

            command, payload = msg
            text = payload.decode("utf-8", errors="replace")

            if command == "CMD":
                if text.strip().lower() == "/quit":
                    proto.send_message(sock, "TEXT", "Goodbye!".encode())
                    print(f"[-] {username} left with /quit")
                    break
                response = handle_command(text)
                proto.send_message(sock, "TEXT", response.encode())
            else:
                proto.send_message(sock, "ERRO", f"unknown command {command}".encode())
                command, payload = msg
                print(f"[debug] получено command={command!r}, payload={payload!r}")
                

    except ConnectionResetError:
        print(f"[!] {username} - connection reset (RST)")
    except BrokenPipeError:
        print(f"[!] {username} - broken pipe")
    finally:
        with clients_lock:
            clients.pop(sock, None)
        sock.close()
        print(f"- Connection with {username} closed")


def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((HOST, PORT))
        server.listen()
        print(f"* Server listening {HOST}:{PORT}")
        while True:
            client_sock, addr = server.accept()
            threading.Thread(
                target=handle_client, args=(client_sock, addr), daemon=True
            ).start()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n* Server has stopped")