import sys

from PyQt6.QtWidgets import QApplication, QHBoxLayout, QLabel, \
                            QVBoxLayout, QWidget, QLineEdit, \
                            QRadioButton, QButtonGroup, QCheckBox, \
                            QTextEdit, QPushButton

app = QApplication(sys.argv)

window = QWidget()
window.setWindowTitle("Профиль пользователя")
window.resize(500, 600)

main_layout = QVBoxLayout()
main_layout.addWidget(QLabel("Create your profile"))
window.setLayout(main_layout)

name_layout = QHBoxLayout()
name_layout.addWidget(QLabel("Name:"))
name_input = QLineEdit()
name_layout.addWidget(name_input)
main_layout.addLayout(name_layout)

age_layout = QHBoxLayout()
age_layout.addWidget(QLabel("Age:"))
age_input = QLineEdit()
age_layout.addWidget(age_input)
main_layout.addLayout(age_layout)

main_layout.addWidget(QLabel("Work format:"))
work_layout = QHBoxLayout()
        
rb_office = QRadioButton("Office")
rb_remote = QRadioButton("Remote")
rb_hybrid = QRadioButton("Hybrid")

work_group = QButtonGroup()
work_group.addButton(rb_office)
work_group.addButton(rb_remote)
work_group.addButton(rb_hybrid)

rb_remote.setChecked(True) 

work_layout.addWidget(rb_office)
work_layout.addWidget(rb_remote)
work_layout.addWidget(rb_hybrid)
main_layout.addLayout(work_layout)

notif_checkbox = QCheckBox("Receive notifications")
notif_checkbox.setChecked(True)
main_layout.addWidget(notif_checkbox)

main_layout.addWidget(QLabel("About:"))
about_input = QTextEdit()
main_layout.addWidget(about_input)

result_label = QLabel("Здесь появится результат...")
result_label.setWordWrap(True)

def generate_profile():        
    work_format = "Не выбран"
    if rb_office.isChecked():
        work_format = "Office"
    elif rb_remote.isChecked():
        work_format = "Remote"
    elif rb_hybrid.isChecked():
        work_format = "Hybrid"
        
    notifications = "Yes" if notif_checkbox.isChecked() else "No"

    result_text = (
        f"Name: {name_input.text()}\n"
        f"Age: {age_input.text()}\n"
        f"Work format: {work_format}\n"
        f"Notifications: {notifications}\n\n"
        f"About:\n{about_input.toPlainText()}"
    )
    
    result_label.setText(result_text)

btn_create = QPushButton("Create profile")
btn_create.clicked.connect(generate_profile) 
main_layout.addWidget(btn_create)

main_layout.addWidget(QLabel("Result:"))

main_layout.addWidget(result_label) 

window.show()
sys.exit(app.exec())