from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QMessageBox, QTextEdit
from PyQt6.QtCore import Qt, QSignalBlocker
import os
import logging
from .scope_widget import ScopeWidget

logger = logging.getLogger(__name__)

class ClearWhitespaceDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Clear Leading/Trailing Whitespace")
        self.text_editor_panel = self.parent().text_editor_panel

        main_layout = QVBoxLayout(self)
        form_layout = QVBoxLayout()
        button_layout = QHBoxLayout()

        self.scope_widget = ScopeWidget(self)
        self.apply_button = QPushButton("Apply")

        form_layout.addWidget(self.scope_widget)

        button_layout.addStretch()
        button_layout.addWidget(self.apply_button)

        main_layout.addLayout(form_layout)
        main_layout.addLayout(button_layout)

        self.apply_button.clicked.connect(self.apply_changes)

    def apply_changes(self):
        targets_to_modify = self.scope_widget.get_targets()
        if not targets_to_modify:
            return

        scope_index = self.scope_widget.scope_combo.currentIndex()
        if scope_index in [2, 3]:
            reply = QMessageBox.question(self, 'Confirm Apply to All',
                                         f"Are you sure you want to clear whitespace in ALL {len(targets_to_modify)} targeted text files?\n\nThis action is irreversible.",
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                         QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.No:
                return

        modified_files = set()
        for target in targets_to_modify:
            file_path = None
            original_text = None

            if isinstance(target, QTextEdit):
                editor = target
                file_path = next((path for path, ed in self.text_editor_panel.text_editors.items() if ed == editor), None)
                if not file_path:
                    logger.warning(f"Could not find path for editor: {editor}")
                    continue
                original_text = editor.toPlainText()
            
            elif isinstance(target, str):
                file_path = target
                if file_path in self.parent().app_state.text_cache:
                    original_text = self.parent().app_state.text_cache[file_path]
                else:
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            original_text = f.read()
                    except Exception as e:
                        logger.error(f"Could not read file {file_path}: {e}")
                        continue
            
            if file_path is None or original_text is None:
                continue

            new_text = original_text.strip()

            if new_text != original_text:
                self.parent().on_text_modified(file_path, new_text)
                modified_files.add(file_path)

                open_editor = self.text_editor_panel.text_editors.get(file_path)
                if open_editor:
                    blocker = QSignalBlocker(open_editor)
                    open_editor.setPlainText(new_text)

        modified_files_count = len(modified_files)
        if modified_files_count > 0:
            QMessageBox.information(self, 'Apply Complete', f"Successfully cleared whitespace in {modified_files_count} file(s).")
        else:
            QMessageBox.information(self, 'No Changes', "No leading or trailing whitespace was found in the targeted files.")

        self.close()