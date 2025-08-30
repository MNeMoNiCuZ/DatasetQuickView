from PyQt6.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QSplitter, QToolBar, QCheckBox, QSizePolicy, QPushButton, QFrame, QMessageBox, QFileDialog, QLabel, QListWidget, QTextEdit, QDialog, QLineEdit, QStackedWidget, QStyle
from PyQt6.QtGui import QShortcut, QKeySequence, QFont, QIcon, QAction
from PyQt6.QtCore import Qt, QEvent, pyqtSignal
import os, sys, subprocess

from .ui.main_window_ui import Ui_MainWindow
from .core.app_state import AppState
from .core.file_operations import FileOperations
from .core.dialog_manager import DialogManager
from .core.hotkey_manager import HotkeyManager
from .core.settings_manager import SettingsManager

class MainWindow(QMainWindow, Ui_MainWindow):
    file_loaded = pyqtSignal()

    def __init__(self, folder_path, config):
        super().__init__()
        self.config = config
        self.app_state = AppState(folder_path, config)
        
        self.setupUi(self)
        
        self.file_operations = FileOperations(self.app_state, self)
        self.dialog_manager = DialogManager(self)
        self.hotkey_manager = HotkeyManager(self)
        self.settings_manager = SettingsManager(self)

        self.setWindowTitle(f"DatasetQuickView - {self.app_state.folder_path}")
        self.resize(1200, 800)
        
        if getattr(sys, 'frozen', False):
            icon_path = os.path.join(sys._MEIPASS, 'DatasetQuickView_ICON.ico')
        else:
            icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'DatasetQuickView_ICON.ico')
        self.setWindowIcon(QIcon(icon_path))

        self.settings_manager.load_settings()
        self.connect_signals()
        self.file_operations.load_dataset(self.recursive_checkbox.isChecked())
        
        self.file_list.dataset = self.app_state.dataset
        self.file_list.populate_list(self.app_state.dataset.keys())
        
        self.hotkey_manager.setup_hotkeys()
        self.apply_font_settings()
        self.center_on_screen()

        if self.app_state.dataset:
            self.file_list.setCurrentRow(0)

    def connect_signals(self):
        self.file_list.currentItemChanged.connect(self.on_file_selected)
        self.file_list.list_widget.itemClicked.connect(self.on_file_clicked)
        self.text_editor_panel.text_modified.connect(self.on_text_modified)
        self.recursive_checkbox.toggled.connect(self.update_status)
        self.file_list.list_widget.viewport().installEventFilter(self)
        self.filename_edit.returnPressed.connect(lambda: self.file_operations.commit_rename(self.filename_edit.text()))
        self.load_folder_button.clicked.connect(self.dialog_manager.open_folder_dialog)
        self.refresh_button.clicked.connect(self.file_operations.refresh_dataset)
        self.open_file_dir_button.clicked.connect(self.open_selected_file_directory_handler)
        self.detach_button.clicked.connect(self.dialog_manager.open_detached_viewer)
        self.settings_button.clicked.connect(self.dialog_manager.open_settings_dialog)
        self.help_button.clicked.connect(self.dialog_manager.show_help_dialog)
        self.save_current_button.clicked.connect(self.file_operations.save_current_item_changes)
        self.save_all_button.clicked.connect(self.file_operations.save_all_changes)
        self.revert_button.clicked.connect(self.file_operations.revert_current_item_changes)
        self.revert_all_button.clicked.connect(self.file_operations.revert_all_changes)
        self.find_replace_button.clicked.connect(self.dialog_manager.open_find_dialog)
        self.prefix_suffix_button.clicked.connect(self.dialog_manager.open_prefix_suffix_dialog)
        self.clear_whitespace_button.clicked.connect(self.dialog_manager.open_clear_whitespace_dialog)

    def on_file_clicked(self, item):
        # This ensures that re-selecting the same item still triggers the focus behavior
        self.on_file_selected(item, None)

    def on_file_selected(self, current_item, previous_item):
        if self.filename_stack.currentWidget() == self.filename_edit:
            self.cancel_rename()
        if previous_item is not None and self.auto_save_checkbox.isChecked():
            self.file_operations.save_item_changes(previous_item.data(Qt.ItemDataRole.UserRole))

        if current_item is None:
            self.media_viewer.clear_media()
            self.text_editor_panel.load_text_files([], self.app_state.current_font_size, self.app_state.text_cache)
            self.filename_label.setText("")
            return

        media_path = current_item.data(Qt.ItemDataRole.UserRole)
        text_paths = self.app_state.dataset.get(media_path, [])

        if not text_paths:
            basename, _ = os.path.splitext(media_path)
            new_txt_path = basename + ".txt"
            text_paths = [new_txt_path]
        
        self.media_viewer.set_media(media_path)
        self.text_editor_panel.load_text_files(text_paths, self.app_state.current_font_size, self.app_state.text_cache)

        base_name = os.path.basename(media_path)
        name, ext = os.path.splitext(base_name)
        self.filename_label.setText(f"<b>{name}</b>{ext}")

        if text_paths:
            self.text_editor_panel.focus_and_move_cursor_to_end(text_paths[0])

        if hasattr(self, 'find_dialog') and self.dialog_manager.find_dialog and self.dialog_manager.find_dialog.isVisible():
            self.dialog_manager.find_dialog.sync_to_media_item(media_path)
        
        if self.app_state.detached_viewer:
            self.app_state.detached_viewer.set_media(media_path)
        self.update_status()
        self.file_loaded.emit()

    def on_text_modified(self, text_path, new_content):
        self.app_state.text_cache[text_path] = new_content
        if text_path not in self.app_state.dirty_files:
            self.app_state.dirty_files.add(text_path)
            media_path = self.file_list.get_media_path_from_text_path(text_path)
            if media_path:
                self.file_list.set_item_dirty(media_path, True)

    def update_status(self):
        current = self.file_list.currentRow()
        total = self.file_list.count()
        title = f"({current + 1} / {total}) - DatasetQuickView - {self.app_state.folder_path}"
        if self.recursive_checkbox.isChecked():
            title += " (Recursive)"
        self.setWindowTitle(title)
        self.file_list.update_progress(current, total)

    def apply_font_settings(self):
        font = QFont()
        font.setPointSize(self.app_state.current_font_size)
        self.file_list.setFont(font)
        self.text_editor_panel.set_font_for_all(font)

    def apply_layout_settings(self):
        file_list_width = int(self.config.get_setting('Program', 'file_list_width', fallback=250))
        text_editor_width = int(self.config.get_setting('Program', 'text_editor_width', fallback=300))
        self.main_splitter.setSizes([file_list_width, self.width() - file_list_width - text_editor_width, text_editor_width])
        self.main_splitter.setStretchFactor(0, 0)
        self.main_splitter.setStretchFactor(1, 1)
        self.main_splitter.setStretchFactor(2, 0)

    def eventFilter(self, source, event):
        if (event.type() == QEvent.Type.MouseButtonDblClick and source == self.filename_label) or \
           (event.type() == QEvent.Type.MouseButtonPress and source == self.edit_icon_label):
            self.start_rename()
            return True
        if event.type() == QEvent.Type.KeyPress and source == self.filename_edit:
            if event.key() == Qt.Key.Key_Escape:
                self.cancel_rename()
                return True
        if event.type() == QEvent.Type.Wheel and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            parent = source.parent()
            if isinstance(parent, QListWidget):
                if parent.viewMode() == QListWidget.ViewMode.IconMode:
                    current_thumb_size = int(self.config.get_setting('FileList', 'thumbnail_size', 80))
                    if event.angleDelta().y() > 0:
                        new_thumb_size = current_thumb_size + 10
                    else:
                        new_thumb_size = max(20, current_thumb_size - 10)
                    self.config.set_setting('FileList', 'thumbnail_size', str(new_thumb_size))
                    self.file_list.apply_view_settings()
                    return True
            elif isinstance(parent, QTextEdit):
                if event.angleDelta().y() > 0:
                    self.app_state.current_font_size += 1
                else:
                    self.app_state.current_font_size = max(6, self.app_state.current_font_size - 1)
                self.apply_font_settings()
                self.config.set_setting('Display', 'font_size', str(self.app_state.current_font_size))
                return True
        return super().eventFilter(source, event)

    def start_rename(self):
        current_item = self.file_list.currentItem()
        if not current_item:
            return
        
        media_path = current_item.data(Qt.ItemDataRole.UserRole)
        base_name = os.path.basename(media_path)
        name, _ = os.path.splitext(base_name)

        self.filename_stack.setCurrentWidget(self.filename_edit)
        self.filename_edit.setText(name)
        self.filename_edit.setFocus()
        self.filename_edit.selectAll()

    def cancel_rename(self):
        self.filename_stack.setCurrentWidget(self.filename_display_widget)

    

    def closeEvent(self, event):
        if self.app_state.dirty_files:
            reply = QMessageBox.question(self, 'Unsaved Changes',
                                       "You have unsaved changes. Do you want to save them before exiting?",
                                       QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel,
                                       QMessageBox.StandardButton.Cancel)

            if reply == QMessageBox.StandardButton.Save:
                self.file_operations.save_all_changes()
                event.accept()
            elif reply == QMessageBox.StandardButton.Discard:
                event.accept()
            else:
                event.ignore()
                return
        
        if self.app_state.detached_viewer:
            self.app_state.detached_viewer.close()
        self.settings_manager.save_settings()
        super().closeEvent(event)

    def center_on_screen(self):
        screen_geo = self.screen().availableGeometry()
        self.move(screen_geo.center() - self.frameGeometry().center())

    def navigate_files(self, delta):
        current_row = self.file_list.currentRow()
        new_row = current_row + delta
        new_row = max(0, min(self.file_list.count() - 1, new_row))
        self.file_list.setCurrentRow(new_row)

    def select_first_item(self):
        self.file_list.setCurrentRow(0)

    def select_last_item(self):
        self.file_list.setCurrentRow(self.file_list.count() - 1)

    def navigate_files_forward(self):
        self.navigate_files(1)

    def navigate_files_backward(self):
        self.navigate_files(-1)

    def open_selected_file_directory_handler(self):
        current_item = self.file_list.currentItem()
        if not current_item:
            self.statusBar().showMessage("No file selected.", 3000)
            return

        media_path = current_item.data(Qt.ItemDataRole.UserRole)
        try:
            open_selected_file_directory(media_path)
        except Exception as e:
            self.statusBar().showMessage(f"Error opening directory: {e}", 5000)