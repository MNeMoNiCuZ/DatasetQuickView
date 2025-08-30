from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QComboBox, QLineEdit, QMessageBox, QTextEdit
from PyQt6.QtCore import Qt
import os
import logging

logger = logging.getLogger(__name__)

class ScopeWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = parent.parent()
        self.text_editor_panel = self.main_window.text_editor_panel

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.scope_combo = QComboBox()
        self.scope_combo.addItems([
            "Current Textarea",
            "Current Item",
            "All Items",
            "All Items of Type(s)"
        ])
        self.scope_combo.setCurrentIndex(2)

        self.extensions_label = QLabel("Extensions (e.g., .txt, .caption):")
        self.extensions_input = QLineEdit()
        self.extensions_input.setPlaceholderText(".txt, .caption")

        layout.addWidget(QLabel("Scope:"))
        layout.addWidget(self.scope_combo)
        layout.addWidget(self.extensions_label)
        layout.addWidget(self.extensions_input)

        self.scope_combo.currentIndexChanged.connect(self.on_scope_changed)
        self.on_scope_changed()

    def on_scope_changed(self):
        is_extensions_scope = self.scope_combo.currentIndex() == 3
        self.extensions_label.setVisible(is_extensions_scope)
        self.extensions_input.setVisible(is_extensions_scope)

    def get_targets(self):
        scope_index = self.scope_combo.currentIndex()

        if scope_index == 3: # All text files of extension type(s)
            extensions_str = self.extensions_input.text()
            if not extensions_str.strip():
                QMessageBox.warning(self, "No Extensions", "Please enter one or more extensions.")
                return []
            
            target_extensions = {f".{ext.strip().lstrip('.')}".lower() for ext in extensions_str.split(',')}
            
            matching_files = []
            for text_paths in self.main_window.app_state.dataset.values():
                for path in text_paths:
                    _, ext = os.path.splitext(path)
                    if ext.lower() in target_extensions:
                        matching_files.append(path)
            return matching_files
        
        if scope_index == 2: # All text files in dataset
            all_text_files = []
            for text_paths in self.main_window.app_state.dataset.values():
                all_text_files.extend(text_paths)
            return all_text_files

        current_media_item = self.main_window.file_list.currentItem()
        if not current_media_item:
            if scope_index in [0, 1]:
                 QMessageBox.warning(self, "No Item Selected", "Please select an item in the file list first.")
            return []

        if scope_index == 1: # All text files for current item
            media_path = current_media_item.data(Qt.ItemDataRole.UserRole)
            return self.main_window.app_state.dataset.get(media_path, [])

        if scope_index == 0: # Current text box only
            active_editor = self.text_editor_panel.focusWidget()
            if not isinstance(active_editor, QTextEdit):
                QMessageBox.warning(self, "No Active Editor", "Please click on a text box to give it focus before applying.")
                return []
            
            active_path = next((path for path, editor in self.text_editor_panel.text_editors.items() if editor == active_editor), None)
            if active_path:
                return [active_path]
            else:
                logger.warning("Could not find path for the active editor.")
                return []
        
        return []