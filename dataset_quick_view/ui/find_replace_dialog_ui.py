from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QComboBox, QLabel, QCheckBox

class Ui_FindReplaceDialog(object):
    def setupUi(self, FindReplaceDialog):
        FindReplaceDialog.setObjectName("FindReplaceDialog")
        self.main_layout = QVBoxLayout(FindReplaceDialog)
        self.form_layout = QVBoxLayout()
        self.button_layout = QHBoxLayout()

        self.find_input = QLineEdit()
        self.find_input.setPlaceholderText("Find...")
        self.replace_input = QLineEdit()
        self.replace_input.setPlaceholderText("Replace with...")
        
        self.scope_combo = QComboBox()
        self.scope_combo.addItems(["Current file only", "Files with same extension", "All associated files"])
        self.scope_combo.setCurrentIndex(0)

        self.case_sensitive_checkbox = QCheckBox("Case sensitive")
        self.whole_words_checkbox = QCheckBox("Whole words")

        self.status_label = QLabel("Enter text to find.")

        self.find_prev_button = QPushButton("Find Previous")
        self.find_next_button = QPushButton("Find Next")
        self.replace_button = QPushButton("Replace")
        self.replace_button.setEnabled(False)
        self.replace_all_button = QPushButton("Replace All")
        self.replace_all_button.setToolTip("Replace all occurrences in the selected scope.")
        self.replace_and_next_button = QPushButton("Replace && Next")

        self.form_layout.addWidget(QLabel("Find:"))
        self.form_layout.addWidget(self.find_input)
        self.form_layout.addWidget(QLabel("Replace:"))
        self.form_layout.addWidget(self.replace_input)
        self.form_layout.addWidget(QLabel("Scope:"))
        self.form_layout.addWidget(self.scope_combo)
        self.form_layout.addWidget(self.case_sensitive_checkbox)
        self.form_layout.addWidget(self.whole_words_checkbox)
        self.form_layout.addWidget(self.status_label)

        self.button_layout.addStretch()
        self.button_layout.addWidget(self.find_prev_button)
        self.button_layout.addWidget(self.find_next_button)
        self.button_layout.addWidget(self.replace_button)
        self.button_layout.addWidget(self.replace_and_next_button)
        self.button_layout.addWidget(self.replace_all_button)

        self.main_layout.addLayout(self.form_layout)
        self.main_layout.addLayout(self.button_layout)
