from PyQt6.QtWidgets import QDialog, QMessageBox, QTextEdit
from PyQt6.QtGui import QTextDocument, QTextCursor
from PyQt6.QtCore import Qt, QTimer
import os
import logging
import re

from ..ui.find_replace_dialog_ui import Ui_FindReplaceDialog

logger = logging.getLogger(__name__)

class FindReplaceDialog(QDialog, Ui_FindReplaceDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.setWindowTitle("Find and Replace")
        self.main_window = parent
        self.text_editor_panel = self.main_window.text_editor_panel

        self.global_search_results = []
        self.current_result_index = -1
        self.search_direction = 0
        self.search_pending = False
        self.is_jumping = False

        self.search_update_timer = QTimer(self)
        self.search_update_timer.setSingleShot(True)
        self.search_update_timer.setInterval(200)

        self.find_input.textChanged.connect(self.update_find_count)
        self.case_sensitive_checkbox.stateChanged.connect(self.update_highlights_for_all_editors)
        self.whole_words_checkbox.stateChanged.connect(self.update_highlights_for_all_editors)
        self.find_next_button.clicked.connect(self.find_next)
        self.find_prev_button.clicked.connect(self.find_previous)
        self.replace_button.clicked.connect(self.replace_one)
        self.replace_and_next_button.clicked.connect(self.replace_and_find_next)
        self.replace_all_button.clicked.connect(self.replace_all)
        self.main_window.file_loaded.connect(self.resume_search)
        self.text_editor_panel.text_modified.connect(self.on_external_text_change)
        self.search_update_timer.timeout.connect(self._perform_search_update)

    def showEvent(self, event):
        super().showEvent(event)
        self.update_highlights_for_all_editors()
        for editor in self.text_editor_panel.get_all_editors():
            try:
                editor.selectionChanged.disconnect(self.text_editor_panel._on_selection_changed)
            except TypeError:
                pass
            editor.selectionChanged.connect(self._update_replace_button_state)

    def closeEvent(self, event):
        self.text_editor_panel.clear_highlights()
        for editor in self.text_editor_panel.get_all_editors():
            try:
                editor.selectionChanged.disconnect(self._update_replace_button_state)
            except TypeError:
                pass
            editor.selectionChanged.connect(self.text_editor_panel._on_selection_changed)
        try:
            self.text_editor_panel.text_modified.disconnect(self.on_external_text_change)
        except TypeError:
            pass
        super().closeEvent(event)

    def sync_to_media_item(self, media_path):
        """Resets the search context to the specified media item."""
        if self.is_jumping: # If we are in the middle of a jump, do nothing
            return
            
        if not self.find_input.text() or not self.global_search_results:
            return

        # Find the index of the first result that belongs to the new media item
        new_index = -1
        for i, result in enumerate(self.global_search_results):
            res_media_path, _text_path, _pos, _len = result
            if res_media_path == media_path:
                new_index = i
                break  # Stop at the first match on the new item

        if new_index != -1:
            # A match exists on the newly selected item. Jump to it.
            self.current_result_index = new_index
            self._jump_to_result(self.current_result_index)
        else:
            # No match on the new item. Clear highlights and disable buttons.
            self.current_result_index = -1
            self.text_editor_panel.clear_highlights()
            self.replace_button.setEnabled(False)
            self.replace_and_next_button.setEnabled(False)
            # Update status label to be more informative
            total_found = len(self.global_search_results)
            self.status_label.setText(f"Found {total_found} total. No matches on current item.")

    def _update_replace_button_state(self):
        editor = self.sender()
        if not isinstance(editor, QTextEdit):
             # If signal is not from an editor, check the focused widget
            editor = self.text_editor_panel.get_current_editor()
            if not isinstance(editor, QTextEdit):
                return

        enable = False
        cursor = editor.textCursor()
        selected_text = cursor.selectedText()
        find_text = self.find_input.text()
        if find_text and selected_text:
            if self.case_sensitive_checkbox.isChecked():
                enable = selected_text == find_text
            else:
                enable = selected_text.lower() == find_text.lower()
        self.replace_button.setEnabled(enable)
        self.replace_and_next_button.setEnabled(enable)

    def update_highlights_for_all_editors(self):
        find_text = self.find_input.text()
        case_sensitive = self.case_sensitive_checkbox.isChecked()
        whole_words = self.whole_words_checkbox.isChecked()
        for editor in self.text_editor_panel.get_all_editors():
            self.text_editor_panel.highlight_occurrences(editor, find_text, -1, case_sensitive, whole_words)

    def update_find_count(self, text):
        self.current_result_index = -1
        self.search_pending = False
        self.search_direction = 0
        
        self.update_highlights_for_all_editors()

        if not text:
            self.global_search_results = []
            self.main_window.file_list.set_find_results(set())
            self.status_label.setText("Enter text to find.")
            self.replace_button.setEnabled(False)
            self.replace_and_next_button.setEnabled(False)
            return
        
        self._build_global_search_index(text)
        total_found = len(self.global_search_results)
        
        if total_found > 0:
            # Try to find the first result on the current media item
            current_media_item = self.main_window.file_list.currentItem()
            if current_media_item:
                current_media_path = current_media_item.data(Qt.ItemDataRole.UserRole)
                for i, result in enumerate(self.global_search_results):
                    if result[0] == current_media_path:
                        self.current_result_index = i
                        self._jump_to_result(i)
                        return # We're done, _jump_to_result will update the status

        # If no result on current item, or no item selected, just show total.
        self.status_label.setText(f"Found {total_found} occurrence(s)." if total_found > 0 else "No occurrences found.")
        self._update_replace_button_state()


    def _build_global_search_index(self, find_text):
        self.global_search_results = []
        if not find_text: 
            self.main_window.file_list.set_find_results(set())
            return

        find_flags = QTextDocument.FindFlag(0)
        if self.case_sensitive_checkbox.isChecked():
            find_flags |= QTextDocument.FindFlag.FindCaseSensitively
        if self.whole_words_checkbox.isChecked():
            find_flags |= QTextDocument.FindFlag.FindWholeWords

        for media_path, text_paths in self.main_window.app_state.dataset.items():
            for text_path in text_paths:
                editor = self.text_editor_panel.text_editors.get(text_path)
                if editor:
                    content = editor.toPlainText()
                elif text_path in self.main_window.app_state.text_cache:
                    content = self.main_window.app_state.text_cache[text_path]
                else:
                    content = self._read_file_content(text_path)
                if content is None: continue
                
                doc = QTextDocument()
                doc.setPlainText(content)
                cursor = QTextCursor(doc)
                while True:
                    cursor = doc.find(find_text, cursor, find_flags)
                    if cursor.isNull():
                        break
                    self.global_search_results.append((media_path, text_path, cursor.selectionStart(), cursor.selectionEnd() - cursor.selectionStart()))
        
        self.global_search_results.sort(key=lambda x: (x[0], x[1], x[2]))
        
        found_media_files = {result[0] for result in self.global_search_results}
        self.main_window.file_list.set_find_results(found_media_files)

    def _read_file_content(self, path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            logger.warning(f"Could not read file {path}: {e}")
            return None

    def _find_operation(self, find_backwards):
        if not self.global_search_results:
            self._update_status_label()
            return

        self.search_direction = -1 if find_backwards else 1

        if self.current_result_index == -1:
            # No active selection, so find the next result relative to the current view.
            current_media_item = self.main_window.file_list.currentItem()
            if not current_media_item:
                return
            current_media_path = current_media_item.data(Qt.ItemDataRole.UserRole)

            next_index = -1
            if find_backwards:
                # Find the last result that is chronologically BEFORE the current media path.
                for i in range(len(self.global_search_results) - 1, -1, -1):
                    if self.global_search_results[i][0] < current_media_path:
                        next_index = i
                        break
                if next_index == -1: # Wrap around
                    next_index = len(self.global_search_results) - 1
            else:  # Find forwards
                # Find the first result that is on or after the current media path.
                for i, result in enumerate(self.global_search_results):
                    if result[0] >= current_media_path:
                        next_index = i
                        break
                if next_index == -1: # Wrap around
                    next_index = 0
            self.current_result_index = next_index
        else:
            # Standard logic: just move to the next/previous index in the list.
            self.current_result_index = (self.current_result_index + self.search_direction) % len(self.global_search_results)

        self._jump_to_result(self.current_result_index)

    def _jump_to_result(self, index):
        if not (0 <= index < len(self.global_search_results)):
            return

        self.is_jumping = True  # Set the flag before changing the file list
        media_path, text_path, position, length = self.global_search_results[index]
        
        current_media_item = self.main_window.file_list.currentItem()
        current_media_path = current_media_item.data(Qt.ItemDataRole.UserRole) if current_media_item else None

        if current_media_path != media_path:
            self.search_pending = True
            for i in range(self.main_window.file_list.count()):
                item = self.main_window.file_list.list_widget.item(i)
                if item and item.data(Qt.ItemDataRole.UserRole) == media_path:
                    self.main_window.file_list.setCurrentRow(i)
                    break
        else:
            self._highlight_result(text_path, position, length)
        
        self._update_status_label()
        self.is_jumping = False # Reset the flag

    def _highlight_result(self, text_path, position, length):
        editor = self.text_editor_panel.text_editors.get(text_path)
        if editor:
            find_text = self.find_input.text()
            case_sensitive = self.case_sensitive_checkbox.isChecked()
            whole_words = self.whole_words_checkbox.isChecked()
            
            for ed in self.text_editor_panel.get_all_editors():
                current_pos_in_editor = position if ed == editor else -1
                self.text_editor_panel.highlight_occurrences(ed, find_text, current_pos_in_editor, case_sensitive, whole_words)

            cursor = editor.textCursor()
            cursor.setPosition(position)
            cursor.movePosition(QTextCursor.MoveOperation.Right, QTextCursor.MoveMode.KeepAnchor, length)
            editor.setTextCursor(cursor)
            editor.ensureCursorVisible()
            editor.setFocus()
            self._update_replace_button_state()

    def _update_status_label(self):
        total_found = len(self.global_search_results)
        if not self.find_input.text():
            self.status_label.setText("Enter text to find.")
            return

        if total_found == 0:
            self.status_label.setText("No occurrences found.")
            return

        if self.current_result_index != -1:
            self.status_label.setText(f"Viewing {self.current_result_index + 1} of {total_found}.")
        else:
            self.status_label.setText(f"Found {total_found} total. No match on current item.")

    def find_next(self):
        self._find_operation(find_backwards=False)

    def find_previous(self):
        self._find_operation(find_backwards=True)

    def _get_find_flags(self):
        find_flags = QTextDocument.FindFlag(0)
        if self.case_sensitive_checkbox.isChecked():
            find_flags |= QTextDocument.FindFlag.FindCaseSensitively
        if self.whole_words_checkbox.isChecked():
            find_flags |= QTextDocument.FindFlag.FindWholeWords
        return find_flags

    def resume_search(self):
        if self.search_pending:
            self.search_pending = False
            self.update_highlights_for_all_editors()
            self._jump_to_result(self.current_result_index)

    def on_external_text_change(self, file_path, new_content):
        if self.isVisible() and self.find_input.text():
            self.search_update_timer.start()

    def _perform_search_update(self):
        self.update_find_count(self.find_input.text())

    def replace_one(self):
        if self.current_result_index == -1:
            return

        _media_path, text_path, position, length = self.global_search_results[self.current_result_index]
        editor = self.text_editor_panel.text_editors.get(text_path)
        if not editor:
            logger.warning(f"Editor not found for path {text_path} during replace.")
            return

        cursor = editor.textCursor()
        cursor.setPosition(position)
        cursor.movePosition(QTextCursor.MoveOperation.Right, QTextCursor.MoveMode.KeepAnchor, length)
        
        # Ensure the selection in the editor matches the find text before replacing
        find_text = self.find_input.text()
        selected_text = cursor.selectedText()
        
        matches = False
        if self.case_sensitive_checkbox.isChecked():
            matches = (selected_text == find_text)
        else:
            matches = (selected_text.lower() == find_text.lower())

        if not matches:
            logger.warning("Editor content out of sync with search index. Rebuilding.")
            self.update_find_count(find_text)
            QMessageBox.information(self, "Search Index Synced", "Editor content has changed. Please try your action again.")
            return

        replace_text = self.replace_input.text()
        cursor.insertText(replace_text)

        # Invalidate the current index and rebuild to reflect the change
        self.update_find_count(find_text)

    def replace_and_find_next(self):
        if self.current_result_index == -1:
            self.find_next()
            return

        # Get info about the item being replaced BEFORE the edit.
        old_media_path, old_text_path, old_position, old_length = self.global_search_results[self.current_result_index]
        
        editor = self.text_editor_panel.text_editors.get(old_text_path)
        if not editor: return

        # Perform the replacement.
        cursor = editor.textCursor()
        cursor.setPosition(old_position)
        cursor.movePosition(QTextCursor.MoveOperation.Right, QTextCursor.MoveMode.KeepAnchor, old_length)
        cursor.insertText(self.replace_input.text())

        # Rebuild the index.
        find_text = self.find_input.text()
        self._build_global_search_index(find_text)
        self._update_status_label()

        if not self.global_search_results:
            self.current_result_index = -1
            self.update_highlights_for_all_editors()
            return

        # Find the first result that is strictly after the one we just replaced.
        next_index = -1
        for i, result in enumerate(self.global_search_results):
            media_path, text_path, position, _ = result
            if media_path > old_media_path:
                next_index = i
                break
            if media_path == old_media_path:
                if text_path > old_text_path:
                    next_index = i
                    break
                if text_path == old_text_path:
                    if position > old_position:
                        next_index = i
                        break
        
        # If no such item is found, wrap around to the beginning.
        if next_index == -1:
            next_index = 0

        self.current_result_index = next_index
        self._jump_to_result(self.current_result_index)

    def replace_all(self):
        find_text = self.find_input.text()
        replace_text = self.replace_input.text()
        if not find_text or not self.global_search_results:
            return

        # Group replacements by file path
        replacements_by_file = {}
        for media_path, text_path, position, length in self.global_search_results:
            if text_path not in replacements_by_file:
                replacements_by_file[text_path] = []
            replacements_by_file[text_path].append((position, length))

        total_replacements = 0
        files_changed = 0

        confirm_message = (
            f"Are you sure you want to replace all {len(self.global_search_results)} occurrences of '{find_text}' "
            f"with '{replace_text}' in {len(replacements_by_file)} file(s)?\n\n"
            "This action is irreversible."
        )
        reply = QMessageBox.question(self, 'Confirm Replace All', confirm_message,
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.No:
            self.status_label.setText("Replace all cancelled.")
            return

        for file_path, replacements in replacements_by_file.items():
            try:
                # Read from cache if available, otherwise from disk
                if file_path in self.main_window.app_state.text_cache:
                    content = self.main_window.app_state.text_cache[file_path]
                else:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()

                # Apply replacements from the end to avoid shifting indices
                replacements.sort(key=lambda x: x[0], reverse=True)
                
                count_in_file = 0
                for pos, length in replacements:
                    # Check if the text to be replaced still matches the find_text
                    # This is a safeguard against replacing the wrong text if the file has changed
                    if content[pos:pos+length].lower() == find_text.lower() or \
                       (self.case_sensitive_checkbox.isChecked() and content[pos:pos+length] == find_text):
                        content = content[:pos] + replace_text + content[pos+length:]
                        count_in_file += 1

                if count_in_file > 0:
                    total_replacements += count_in_file
                    files_changed += 1
                    # Write back to disk
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    
                    # Update editor if open
                    editor = self.text_editor_panel.text_editors.get(file_path)
                    if editor:
                        editor.blockSignals(True)
                        cursor_pos = editor.textCursor().position()
                        editor.setPlainText(content)
                        cursor = editor.textCursor()
                        cursor.setPosition(cursor_pos)
                        editor.setTextCursor(cursor)
                        editor.blockSignals(False)

                    # Update cache
                    self.main_window.app_state.text_cache[file_path] = content

            except Exception as e:
                logger.error(f"Error processing file {file_path}: {e}")
                QMessageBox.warning(self, "Error", f"Could not process file: {file_path}\n{e}")

        self.status_label.setText(f"Made {total_replacements} replacement(s) in {files_changed} file(s).")
        self.update_find_count(self.find_input.text())

    def _get_files_from_scope(self):
        scope_index = self.scope_combo.currentIndex()
        all_files = list(self.main_window.app_state.dataset.keys())

        if scope_index == 2: # All associated files
            all_text_files = []
            for media_path in all_files:
                all_text_files.extend(self.main_window.app_state.dataset[media_path])
            return all_text_files

        current_media_item = self.main_window.file_list.currentItem()
        if not current_media_item:
            return []
        current_media_path = current_media_item.data(Qt.ItemDataRole.UserRole)
        
        if scope_index == 0: # Current file only
            return self.main_window.app_state.dataset.get(current_media_path, [])

        if scope_index == 1: # Files with same extension
            _, current_ext = os.path.splitext(current_media_path)
            same_ext_files = []
            for media_path in all_files:
                if media_path.endswith(current_ext):
                    same_ext_files.extend(self.main_window.app_state.dataset[media_path])
            return same_ext_files
        
        return []
