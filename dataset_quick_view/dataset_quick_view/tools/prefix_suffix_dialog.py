from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QLabel, QComboBox, QMessageBox, QTextEdit
from PyQt6.QtCore import Qt
import os
import logging

logger = logging.getLogger(__name__)

class PrefixSuffixDialog(QDialog):
    _last_prefix = "" # Class variable to store last used prefix
    _last_suffix = "" # Class variable to store last used suffix

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Prefix/Suffix")
        self.text_editor_panel = self.parent().text_editor_panel

        # Layouts
        main_layout = QVBoxLayout(self)
        form_layout = QVBoxLayout()
        button_layout = QHBoxLayout()

        # Widgets
        self.prefix_input = QLineEdit()
        self.prefix_input.setPlaceholderText("Enter prefix...")
        self.suffix_input = QLineEdit()
        self.suffix_input.setPlaceholderText("Enter suffix...")
        
        # Set last used values
        self.prefix_input.setText(PrefixSuffixDialog._last_prefix)
        self.suffix_input.setText(PrefixSuffixDialog._last_suffix)
        
        self.scope_combo = QComboBox()
        self.scope_combo.addItems(["Current file only", "Files with same extension", "All associated files"])
        self.scope_combo.setCurrentIndex(2) # Default to "All associated files"

        self.apply_button = QPushButton("Apply")

        # Add widgets to layouts
        form_layout.addWidget(QLabel("Prefix:"))
        form_layout.addWidget(self.prefix_input)
        form_layout.addWidget(QLabel("Suffix:"))
        form_layout.addWidget(self.suffix_input)
        form_layout.addWidget(QLabel("Scope:"))
        form_layout.addWidget(self.scope_combo)

        button_layout.addStretch()
        button_layout.addWidget(self.apply_button)

        main_layout.addLayout(form_layout)
        main_layout.addLayout(button_layout)

        # Connect signals
        self.apply_button.clicked.connect(self.apply_changes)

    def apply_changes(self):
        prefix = self.prefix_input.text()
        suffix = self.suffix_input.text()
        scope_index = self.scope_combo.currentIndex()
        
        targets_to_modify = self._get_editors_from_scope()

        if scope_index == 2: # All associated files - require confirmation
            reply = QMessageBox.question(self, 'Confirm Apply to All',
                                         f"Are you sure you want to add prefix/suffix to ALL {len(targets_to_modify)} associated text files?",
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                         QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.No:
                logger.debug("Apply to All cancelled by user.")
                return

        modified_files_count = 0
        for target in targets_to_modify:
            if isinstance(target, QTextEdit): # It's a QTextEdit object (for current file or same extension)
                editor = target
                current_text_path = next((path for path, ed in self.text_editor_panel.text_editors.items() if ed == editor), None)
                if not current_text_path:
                    logger.warning(f"Could not find path for editor: {editor}")
                    continue

                original_text = editor.toPlainText()
                new_text = f"{prefix}{original_text}{suffix}"
                editor.setPlainText(new_text) # Update in-memory editor

                # Save to disk
                try:
                    with open(current_text_path, 'w', encoding='utf-8') as f:
                        f.write(new_text)
                    logger.debug(f"Applied prefix/suffix to editor and saved to {current_text_path}")
                    modified_files_count += 1
                except Exception as e:
                    logger.error(f"Error saving modified content to {current_text_path}: {e}")

            elif isinstance(target, str): # It's a file path (for All associated files)
                file_path = target
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        original_text = f.read()
                    
                    new_text = f"{prefix}{original_text}{suffix}"

                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(new_text)
                    logger.debug(f"Applied prefix/suffix to file: {file_path}")
                    modified_files_count += 1
                except Exception as e:
                    logger.error(f"Error processing file {file_path} for prefix/suffix: {e}")
        
        # Refresh the currently displayed editor if its file was modified
        current_media_item = self.parent().file_list.currentItem()
        if current_media_item:
            current_media_path = current_media_item.data(Qt.ItemDataRole.UserRole) # Need Qt imported
            if current_media_path in self.parent().dataset:
                text_paths_for_current_media = self.parent().dataset[current_media_path]
                for text_path in text_paths_for_current_media:
                    editor_to_refresh = self.text_editor_panel.text_editors.get(text_path)
                    if editor_to_refresh and text_path in targets_to_modify: # Only refresh if it was modified
                        try:
                            with open(text_path, 'r', encoding='utf-8') as f:
                                updated_content = f.read()
                            editor_to_refresh.setPlainText(updated_content)
                            logger.debug(f"Refreshed editor content for {text_path}")
                        except Exception as e:
                            logger.error(f"Error refreshing editor content for {text_path}: {e}")

        QMessageBox.information(self, 'Apply Complete', f"Successfully applied prefix/suffix to {modified_files_count} file(s).")
        
        # Store current values for session persistence
        PrefixSuffixDialog._last_prefix = prefix
        PrefixSuffixDialog._last_suffix = suffix

        self.close()

    def closeEvent(self, event):
        # Store current values for session persistence when dialog is closed by any means
        PrefixSuffixDialog._last_prefix = self.prefix_input.text()
        PrefixSuffixDialog._last_suffix = self.suffix_input.text()
        super().closeEvent(event)

    def _get_editors_from_scope(self):
        scope_index = self.scope_combo.currentIndex()
        all_editors = self.text_editor_panel.text_editors
        
        if scope_index == 2: # All associated files
            all_text_files = []
            # Access main_window.dataset through parent
            for media_path, text_paths in self.parent().dataset.items():
                all_text_files.extend(text_paths)
            return all_text_files # Return file paths for direct modification

        current_editor = self.text_editor_panel.focusWidget()
        if not isinstance(current_editor, QTextEdit): # Corrected type check
            # Fallback if no QTextEdit has focus, try to get the first available editor
            current_editor = list(all_editors.values())[0] if all_editors else None
            if not current_editor:
                return [] # No editors available

        if scope_index == 0: # Current file only
            return [current_editor]

        if scope_index == 1: # Files with same extension
            current_path = next((path for path, editor in all_editors.items() if editor == current_editor), None)
            if not current_path:
                return [] # Current editor path not found
            
            _, current_ext = os.path.splitext(current_path)
            return [editor for path, editor in all_editors.items() if path.endswith(current_ext)]
        
        return []