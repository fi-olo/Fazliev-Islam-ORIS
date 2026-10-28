import json
import socket
import struct
import sys
from queue import Queue

from PyQt6.QtCore import Qt, pyqtSignal, QThread
from PyQt6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


HOST = "127.0.0.1"
PORT = 50505


class NetCom:
    def __init__(self, sock):
        self.sock = sock

    @staticmethod
    def _recv_exact(sock, size):
        chunks = []
        received = 0
        while received < size:
            chunk = sock.recv(size - received)
            if not chunk:
                return None
            chunks.append(chunk)
            received += len(chunk)
        return b"".join(chunks)

    def recv(self):
        header = self._recv_exact(self.sock, 4)
        if header is None:
            return None

        payload_size = struct.unpack("!I", header)[0]
        payload = self._recv_exact(self.sock, payload_size)
        if payload is None:
            return None

        return json.loads(payload.decode("utf-8"))

    def send(self, message):
        payload = json.dumps(message, ensure_ascii=False).encode("utf-8")
        header = struct.pack("!I", len(payload))
        self.sock.sendall(header + payload)


class ReceiveThread(QThread):
    message_received = pyqtSignal(dict)
    connection_lost = pyqtSignal(str)

    def __init__(self, net):
        super().__init__()
        self.net = net

    def run(self):
        try:
            while True:
                message = self.net.recv()
                if message is None:
                    self.connection_lost.emit("Сервер закрыл соединение")
                    break
                self.message_received.emit(message)
        except (OSError, ConnectionError) as e:
            self.connection_lost.emit(f"Соединение потеряно: {e}")


class SendThread(QThread):
    def __init__(self, net):
        super().__init__()
        self.net = net
        self.queue = Queue()

    def send(self, message):
        self.queue.put(message)

    def stop(self): 
        self.queue.put(None)

    def run(self):
        while True:
            message = self.queue.get()
            if message is None:
                break
            try:
                self.net.send(message)
            except (ConnectionError, OSError):
                break


class MainWindow(QMainWindow):
    def __init__(self, net):
        super().__init__()
        self.net = net

        self.setWindowTitle("PyQt6 network chat")
        self.resize(560, 460)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Ваше имя")
        self.username_input.setText("Гость")

        self.history = QTextEdit()
        self.history.setReadOnly(True)

        self.input = QLineEdit()
        self.input.setPlaceholderText("Type a message…")

        self.send_button = QPushButton("Send")
        self.status_label = QLabel(f"Connected to {HOST}:{PORT}")
        self.status_label.setStyleSheet("color: green;")

        self.clear_button = QPushButton("Clear Hystory")

        name_row = QHBoxLayout()
        name_row.addWidget(QLabel("Имя:"))
        name_row.addWidget(self.username_input)

        input_row = QHBoxLayout()
        input_row.addWidget(self.input)
        input_row.addWidget(self.send_button)

        layout = QVBoxLayout()
        layout.addWidget(self.status_label)
        layout.addLayout(name_row)
        layout.addWidget(self.history)
        layout.addLayout(input_row)
        layout.addWidget(self.clear_button)

        root = QWidget()
        root.setLayout(layout)
        self.setCentralWidget(root)

        self.send_button.clicked.connect(self.on_send_clicked)
        self.input.returnPressed.connect(self.on_send_clicked)

        self.clear_button.clicked.connect(self.clear_hystory)

        self.receive_thread = ReceiveThread(self.net)
        self.receive_thread.message_received.connect(self.handle_message)
        self.receive_thread.connection_lost.connect(self.on_connection_lost)
        self.receive_thread.start()

        self.send_thread = SendThread(self.net)
        self.send_thread.start()

    def on_send_clicked(self):
        text = self.input.text().strip()
        if not text:
            return

        username = self.username_input.text().strip() or "Аноним"

        self.send_thread.send({
            "type": "chat",
            "username": username,
            "text": text,
        })
        self.input.clear()

    def handle_message(self, message):
        if message.get("type") == "chat":
            username = message.get("username", "Аноним")
            text = message.get("text", "")
            self.history.append(f"{username}: {text}")
        if message.get("type") == "system": 
            text = message.get("text", "")
            self.history.append(f"[Система] {text}")

    def set_connected(self, connected: bool):
        if connected:
            self.status_label.setText("Connected")
            self.status_label.setStyleSheet("color: green;")
        else:
            self.status_label.setText("Disconnected")
            self.status_label.setStyleSheet("color: red;")

    def on_connection_lost(self, error: str):
        self.set_connected(False)
        self.history.append(f"[Система] {error}")
        self.send_button.setEnabled(False)
        self.input.setEnabled(False)


    def clear_hystory(self): 
        self.history.clear()

    def closeEvent(self, event):
        self.send_thread.stop()
        self.send_thread.wait(2000) 

        try:
            self.net.sock.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass

        self.net.sock.close()

        self.receive_thread.wait(2000)
        event.accept()


def main():
    app = QApplication(sys.argv)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect((HOST, PORT))
    except OSError as e:
        print(f"Could not connect: {e}")
        return

    net = NetCom(sock)
    window = MainWindow(net)
    window.show()
    raise SystemExit(app.exec())


if __name__ == "__main__":
    main()
