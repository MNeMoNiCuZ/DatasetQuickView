from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTextEdit, QLabel, QScrollArea, QFrame, QPushButton, QInputDialog, QMessageBox
from PyQt6.QtGui import QPalette, QColor, QTextCharFormat, QTextCursor, QTextDocument
from PyQt6.QtCore import pyqtSignal, QSignalBlocker, Qt
import os

class TextEditorPanel(QWidget):
    text_modified = pyqtSignal(str, str)  # Signal to emit when text changes (file_path, new_content)

    def __init__(self, main_window=None):
        super().__init__()
        self.setObjectName("TextEditorPanel")
        self.main_window = main_window

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(1, 1, 1, 1)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.main_layout.addWidget(self.scroll_area)

        self.container_widget = QWidget()
        self.scroll_area.setWidget(self.container_widget)
        
        self.editors_layout = QVBoxLayout(self.container_widget)
        self.editors_layout.setContentsMargins(8, 8, 8, 8)
        self.editors_layout.setSpacing(8)

        self.text_editors = {}

        self.primary_highlight_color = QColor("#BDBDBD")
        self.secondary_highlight_color = QColor("#E0E0E0")

    def clear_highlights(self, editor=None):
        editors_to_clear = [editor] if editor else self.text_editors.values()
        for ed in editors_to_clear:
            ed.setExtraSelections([])

    def highlight_occurrences(self, editor, text, current_pos=-1, case_sensitive=False, whole_words=False):
        selections = []
        primary_format = QTextCharFormat()
        primary_format.setBackground(self.primary_highlight_color)
        primary_format.setForeground(QColor("black"))
        
        secondary_format = QTextCharFormat()
        secondary_format.setBackground(self.secondary_highlight_color)
        secondary_format.setForeground(QColor("black"))

        find_flags = QTextDocument.FindFlag(0)
        if case_sensitive:
            find_flags |= QTextDocument.FindFlag.FindCaseSensitively
        if whole_words:
            find_flags |= QTextDocument.FindFlag.FindWholeWords

        cursor = QTextCursor(editor.document())
        while not cursor.isNull() and not cursor.atEnd():
            cursor = editor.document().find(text, cursor, find_flags)
            if not cursor.isNull():
                is_current = cursor.selectionStart() == current_pos
                selection = QTextEdit.ExtraSelection()
                selection.cursor = cursor
                selection.format = primary_format if is_current else secondary_format
                selections.append(selection)
        
        editor.setExtraSelections(selections)

    def _on_selection_changed(self):
        source_editor = self.sender()
        if not isinstance(source_editor, QTextEdit):
            return

        if not source_editor.textCursor().hasSelection():
            for editor in self.get_all_editors():
                self.clear_highlights(editor)
            return

        for editor in self.get_all_editors():
            if editor != source_editor:
                blocker = QSignalBlocker(editor)
                cursor = editor.textCursor()
                if cursor.hasSelection():
                    cursor.clearSelection()
                    editor.setTextCursor(cursor)
                self.clear_highlights(editor)
        
        user_cursor = source_editor.textCursor()
        selected_text = user_cursor.selectedText()

        if len(selected_text) < 2 or selected_text.isspace():
            self.clear_highlights(source_editor)
            return

        secondary_format = QTextCharFormat()
        secondary_format.setBackground(self.secondary_highlight_color)
        secondary_format.setForeground(QColor("black"))
        find_flags = QTextDocument.FindFlag.FindCaseSensitively

        for editor in self.get_all_editors():
            selections = []
            doc_cursor = QTextCursor(editor.document())
            while not doc_cursor.isNull() and not doc_cursor.atEnd():
                doc_cursor = editor.document().find(selected_text, doc_cursor, find_flags)
                if not doc_cursor.isNull():
                    if (editor == source_editor and
                        doc_cursor.selectionStart() == user_cursor.selectionStart() and
                        doc_cursor.selectionEnd() == user_cursor.selectionEnd()):
                        continue

                    selection = QTextEdit.ExtraSelection()
                    selection.cursor = doc_cursor
                    selection.format = secondary_format
                    selections.append(selection)
            
            editor.setExtraSelections(selections)

    def _on_text_changed(self, file_path):
        editor = self.text_editors.get(file_path)
        if editor:
            self.text_modified.emit(file_path, editor.toPlainText())

    def load_text_files(self, file_paths, font_size, text_cache):
        self.clear_highlights()
        for i in reversed(range(self.editors_layout.count())):
            widget = self.editors_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)
        self.text_editors = {}

        if not file_paths:
            self.editors_layout.addWidget(QLabel("No text files for this item. Start typing to create one."))
        else:
            for file_path in file_paths:
                # Check cache first, otherwise read from file
                if file_path in text_cache:
                    content = text_cache[file_path]
                else:
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                    except FileNotFoundError:
                        # This is a new file, start with empty content
                        content = ""
                    except Exception as e:
                        content = f"Error reading file: {e}"
                    # Add to cache regardless of whether it was read or is new
                    text_cache[file_path] = content

                filename = os.path.basename(file_path)
                _, ext = os.path.splitext(filename)
                label = QLabel(f"<b>{ext}</b>")
                editor = QTextEdit()
                editor.viewport().installEventFilter(self.main_window)
                
                font = editor.font()
                font.setPointSize(font_size)
                editor.setFont(font)
                label.setFont(font)

                palette = editor.palette()
                palette.setColor(QPalette.ColorRole.Highlight, QColor('#add8e6'))
                palette.setColor(QPalette.ColorRole.HighlightedText, QColor('#000000'))
                editor.setPalette(palette)

                editor.setPlainText(content)
                editor.setAcceptRichText(False)

                editor.selectionChanged.connect(self._on_selection_changed)
                # Use a lambda to pass the file_path to the slot
                editor.textChanged.connect(lambda fp=file_path: self._on_text_changed(fp))

                self.editors_layout.addWidget(label)
                self.editors_layout.addWidget(editor)
                self.text_editors[file_path] = editor

        # Add the '+' button
        add_button = QPushButton("[ + ]")
        add_button.setToolTip("Add a new text format for the current item.")
        add_button.clicked.connect(self._on_add_new_format_clicked)
        self.editors_layout.addWidget(add_button)

    def set_font_for_all(self, font):
        for editor in self.text_editors.values():
            editor.setFont(font)
        for i in range(self.editors_layout.count()):
            widget = self.editors_layout.itemAt(i).widget()
            if isinstance(widget, QLabel):
                widget.setFont(font)

    def get_all_editors(self):
        return self.text_editors.values()

    def get_current_editor(self):
        return self.focusWidget()

    def focus_and_move_cursor_to_end(self, file_path):
        editor = self.text_editors.get(file_path)
        if editor:
            editor.setFocus()
            cursor = editor.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.End)
            editor.setTextCursor(cursor)
            editor.ensureCursorVisible()

    def _on_add_new_format_clicked(self):
        current_item = self.main_window.file_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "No Item Selected", "Please select a media file first.")
            return

        text, ok = QInputDialog.getText(self, 'Add New Format', 'Enter new extension (e.g., .caption):')
        if ok and text:
            if not text.startswith('.'):
                text = '.' + text
            
            media_path = current_item.data(Qt.ItemDataRole.UserRole)
            base, _ = os.path.splitext(media_path)
            new_text_path = base + text

            # Check if this format already exists for the current item
            if new_text_path in self.text_editors:
                QMessageBox.information(self, "Format Exists", f"The format '{text}' already exists for this item.")
                return

            # Add to dataset and cache
            self.main_window.dataset.setdefault(media_path, []).append(new_text_path)
            self.main_window.text_cache[new_text_path] = ""
            self.main_window.on_text_modified(new_text_path, "") # Mark as dirty

            # Ask to apply to all
            reply = QMessageBox.question(self, 'Apply to All?', 
                                       f"Do you want to create an empty '{text}' file for all other items in the dataset?",
                                       QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                       QMessageBox.StandardButton.No)

            if reply == QMessageBox.StandardButton.Yes:
                for m_path in self.main_window.dataset.keys():
                    if m_path == media_path: continue # Skip current
                    
                    m_base, _ = os.path.splitext(m_path)
                    t_path = m_base + text
                    
                    # Add to dataset if it doesn't exist
                    if t_path not in self.main_window.dataset.get(m_path, []):
                        self.main_window.dataset.setdefault(m_path, []).append(t_path)
                    
                    # Add to cache and mark as dirty if not already there
                    if t_path not in self.main_window.text_cache:
                        self.main_window.text_cache[t_path] = ""
                        self.main_window.on_text_modified(t_path, "")

            # Refresh the view for the current item
            self.main_window.on_file_selected(current_item, None)