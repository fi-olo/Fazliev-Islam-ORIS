import sys
import json
import os

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QTextEdit,
    QRadioButton,
    QCheckBox,
    QPushButton,
    QListWidget,
    QListWidgetItem,
    QComboBox,
    QMessageBox,
    QDialog,
    QDialogButtonBox,
)

DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tasks.json")


class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("О программе")
        self.setMinimumWidth(360)

        layout = QVBoxLayout(self)

        title = QLabel("Task Manager 2.0")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title)

        layout.addWidget(QLabel(
            "Менеджер задач на PyQt6.\n\n"
            "Возможности:\n"
            "> Приоритеты и фильтрация\n"
            "> Удаление выбранной задачи с подтверждением\n"
            "> Редактирование задачи (двойной клик)\n"
            "> Хранение задач в JSON\n"
            "> Пользовательский сигнал task_created"
        ))

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        buttons.accepted.connect(self.accept)
        layout.addWidget(buttons)


class TaskManagerWindow(QMainWindow):
    task_created = pyqtSignal(dict)

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Task Manager")
        self.resize(600, 760)

        self.tasks = []
        self.editing_index = None

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)

        self.title_label = QLabel("Task (0 characters)")
        main_layout.addWidget(self.title_label)

        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Enter task title")
        self.title_input.textChanged.connect(self.update_title_char_count)
        main_layout.addWidget(self.title_input)

        main_layout.addWidget(QLabel("Description"))
        self.description_input = QTextEdit()
        self.description_input.setPlaceholderText("Enter task description")
        main_layout.addWidget(self.description_input)

        main_layout.addWidget(QLabel("Priority"))
        priority_layout = QHBoxLayout()

        self.priority_low = QRadioButton("Low")
        self.priority_medium = QRadioButton("Medium")
        self.priority_high = QRadioButton("High")
        self.priority_medium.setChecked(True)

        priority_layout.addWidget(self.priority_low)
        priority_layout.addWidget(self.priority_medium)
        priority_layout.addWidget(self.priority_high)
        main_layout.addLayout(priority_layout)

        main_layout.addWidget(QLabel("Additional options"))

        self.option_important = QCheckBox("Important")
        self.option_notify = QCheckBox("Send notification")
        self.option_favorite = QCheckBox("Add to favorites")
        main_layout.addWidget(self.option_important)
        main_layout.addWidget(self.option_notify)
        main_layout.addWidget(self.option_favorite)

        buttons_layout = QHBoxLayout()

        self.create_button = QPushButton("Create task")
        self.clear_button = QPushButton("Clear list")
        self.delete_button = QPushButton("Delete last task")
        self.delete_selected_button = QPushButton("Delete selected")
        self.about_button = QPushButton("About")

        self.create_button.clicked.connect(self.create_task)
        self.clear_button.clicked.connect(self.clear_tasks_list)
        self.delete_button.clicked.connect(self.delete_last_task)
        self.delete_selected_button.clicked.connect(self.delete_selected_task)
        self.about_button.clicked.connect(self.show_about_dialog)

        buttons_layout.addWidget(self.create_button)
        buttons_layout.addWidget(self.delete_selected_button)
        buttons_layout.addWidget(self.clear_button)
        buttons_layout.addWidget(self.delete_button)
        buttons_layout.addWidget(self.about_button)
        main_layout.addLayout(buttons_layout)

        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Filter:"))

        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["All", "Low", "Medium", "High"])
        self.filter_combo.currentTextChanged.connect(self.update_list)
        filter_layout.addWidget(self.filter_combo)
        filter_layout.addStretch()

        self.counter_label = QLabel("Created tasks: 0")
        filter_layout.addWidget(self.counter_label)
        main_layout.addLayout(filter_layout)

        self.tasks_list = QListWidget()
        self.tasks_list.itemDoubleClicked.connect(self.edit_selected_task)
        main_layout.addWidget(self.tasks_list)

        self.status_label = QLabel("Status: Ready")
        main_layout.addWidget(self.status_label)

        self.task_created.connect(self.on_task_created)

        self.apply_styles()
        self.load_tasks()

    def on_task_created(self, task):
        self.status_label.setText(f"Status: Task created — {task['title']}")

    def get_priority(self):
        if self.priority_low.isChecked():
            return "Low"
        if self.priority_high.isChecked():
            return "High"
        return "Medium"

    def set_priority(self, priority):
        self.priority_low.setChecked(priority == "Low")
        self.priority_medium.setChecked(priority == "Medium")
        self.priority_high.setChecked(priority == "High")

    def create_task(self):
        title = self.title_input.text().strip()

        if title == "":
            self.status_label.setText("Status: Enter task title")
            QMessageBox.warning(self, "Warning", "Enter task title")
            return

        task = {
            "title": title,
            "description": self.description_input.toPlainText().strip(),
            "priority": self.get_priority(),
            "important": self.option_important.isChecked(),
            "notify": self.option_notify.isChecked(),
            "favorite": self.option_favorite.isChecked(),
        }

        if self.editing_index is not None:
            self.tasks[self.editing_index] = task
            self.status_label.setText("Status: Task updated")
            self.editing_index = None
            self.create_button.setText("Create task")
        else:
            self.tasks.append(task)
            self.task_created.emit(task)

        self.save_tasks()
        self.update_list()
        self.update_counter()
        self.clear_form(keep_status=True)

    def delete_selected_task(self):
        row = self.tasks_list.currentRow()
        if row < 0:
            self.status_label.setText("Status: Select a task to delete")
            return

        item = self.tasks_list.item(row)
        real_index = item.data(0x0100)

        task = self.tasks[real_index]
        reply = QMessageBox.question(
            self,
            "Удаление задачи",
            f"Удалить задачу «{task['title']}»?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            self.status_label.setText("Status: Delete canceled")
            return

        self.tasks.pop(real_index)
        self.save_tasks()
        self.update_list()
        self.update_counter()
        self.status_label.setText("Status: Task deleted")

    def edit_selected_task(self, item):
        real_index = item.data(0x0100)
        task = self.tasks[real_index]

        self.title_input.setText(task["title"])
        self.description_input.setPlainText(task["description"])
        self.set_priority(task["priority"])
        self.option_important.setChecked(task["important"])
        self.option_notify.setChecked(task["notify"])
        self.option_favorite.setChecked(task["favorite"])

        self.editing_index = real_index
        self.create_button.setText("Save changes")
        self.status_label.setText(f"Status: Editing — {task['title']}")

    def show_about_dialog(self):
        AboutDialog(self).exec()

    def clear_tasks_list(self):
        if not self.tasks:
            self.status_label.setText("Status: List is already empty")
            return

        reply = QMessageBox.question(
            self,
            "Подтверждение очистки",
            "Вы уверены, что хотите полностью очистить список задач?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.No:
            self.status_label.setText("Status: Clear canceled")
            return

        self.tasks.clear()
        self.save_tasks()
        self.update_list()
        self.update_counter()
        self.status_label.setText("Status: List cleared")

    def clear_form(self, keep_status=False):
        self.title_input.clear()
        self.description_input.clear()
        self.priority_medium.setChecked(True)
        self.option_important.setChecked(False)
        self.option_notify.setChecked(False)
        self.option_favorite.setChecked(False)
        self.editing_index = None
        self.create_button.setText("Create task")
        if not keep_status:
            self.status_label.setText("Status: Ready")

    def delete_last_task(self):
        if not self.tasks:
            self.status_label.setText("Status: No tasks")
            return

        reply = QMessageBox.question(
            self,
            "Подтверждение удаления",
            "Удалить последнюю добавленную задачу?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.No:
            return

        self.tasks.pop()
        self.save_tasks()
        self.update_list()
        self.update_counter()
        self.status_label.setText("Status: Task deleted")

    def update_list(self):
        self.tasks_list.clear()

        selected = self.filter_combo.currentText()

        for i, task in enumerate(self.tasks):
            if selected != "All" and task["priority"] != selected:
                continue

            text = f"{i + 1}. [{task['priority']}] {task['title']}"
            if task["important"]:
                text += " (Important)"
            if task["notify"]:
                text += " (Notify)"
            if task["favorite"]:
                text += " (Favorite)"

            item = QListWidgetItem(text)
            item.setData(0x0100, i)
            self.tasks_list.addItem(item)

    def update_counter(self):
        self.counter_label.setText(f"Created tasks: {len(self.tasks)}")

    def update_title_char_count(self, text):
        count = len(text.replace(" ", ""))
        self.title_label.setText(f"Task ({count} characters)")

    def save_tasks(self):
        try:
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(self.tasks, f, ensure_ascii=False, indent=2)
        except OSError as e:
            self.status_label.setText(f"Status: Save error — {e}")

    def load_tasks(self):
        if not os.path.exists(DATA_FILE):
            self.update_list()
            self.update_counter()
            return
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list):
                self.tasks = data
        except (OSError, json.JSONDecodeError):
            self.tasks = []

        self.update_list()
        self.update_counter()
        self.status_label.setText(f"Status: Loaded {len(self.tasks)} tasks")

    def apply_styles(self):
        qss = """
            QMainWindow { background-color: #1e1e24; }
            QLabel {
                font-size: 13px; font-weight: bold;
                color: #e1e2e6; margin-top: 5px;
            }
            QLineEdit, QTextEdit {
                background-color: #2a2a32;
                border: 2px solid #3f3f48;
                border-radius: 6px;
                padding: 6px; font-size: 13px; color: #ffffff;
            }
            QLineEdit:focus, QTextEdit:focus { border: 2px solid #10ac84; }
            QLineEdit:disabled, QTextEdit:disabled {
                background-color: #202027;
                color: #6b6b75;
                border-color: #33333b;
            }
            QRadioButton, QCheckBox {
                color: #d1d2d6; font-size: 13px; padding: 5px;
            }
            QRadioButton:disabled, QCheckBox:disabled { color: #6b6b75; }
            QRadioButton::indicator, QCheckBox::indicator {
                width: 16px; height: 16px;
                background-color: #2a2a32;
                border: 2px solid #3f3f48; border-radius: 4px;
            }
            QRadioButton::indicator { border-radius: 9px; }
            QRadioButton::indicator:checked, QCheckBox::indicator:checked {
                background-color: #10ac84; border-color: #10ac84;
            }
            QPushButton {
                background-color: #10ac84; color: white;
                border: none; border-radius: 6px;
                padding: 10px 15px; font-size: 13px; font-weight: bold;
            }
            QPushButton:hover { background-color: #1dd1a1; }
            QPushButton:pressed { background-color: #0f8667; }
            QPushButton:disabled {
                background-color: #2f4f45;
                color: #8a9a94;
            }
            QPushButton#clear_button { background-color: #000000; }
            QPushButton#clear_button:hover { background-color: #222222; }
            QPushButton#clear_button:disabled { background-color: #111111; color: #666666; }
            QListWidget {
                background-color: #2a2a32;
                border: 2px solid #3f3f48;
                border-radius: 8px; padding: 5px;
                font-size: 14px; color: #ffffff;
            }
            QListWidget::item {
                padding: 8px; border-bottom: 1px solid #3f3f48;
            }
            QListWidget::item:hover { background-color: #34343d; }
            QListWidget::item:selected {
                background-color: #10ac84; color: white; border-radius: 4px;
            }
            QComboBox {
                background-color: #2a2a32;
                border: 2px solid #3f3f48; border-radius: 6px;
                padding: 5px; min-width: 90px; color: #ffffff;
            }
            QComboBox:hover { border-color: #10ac84; }
            QComboBox:disabled { color: #6b6b75; }
            QComboBox QAbstractItemView {
                background-color: #2a2a32; color: #ffffff;
                selection-background-color: #10ac84;
            }
            QDialog { background-color: #1e1e24; }
        """
        self.setStyleSheet(qss)
        self.clear_button.setObjectName("clear_button")


def main():
    app = QApplication(sys.argv)
    window = TaskManagerWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()