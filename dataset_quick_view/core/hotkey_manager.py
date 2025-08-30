from PyQt6.QtGui import QShortcut, QKeySequence
from PyQt6.QtCore import Qt

class HotkeyManager:
    def __init__(self, main_window):
        self.main_window = main_window

    def setup_hotkeys(self):
        QShortcut(QKeySequence("Ctrl+S"), self.main_window, self.main_window.file_operations.save_current_item_changes)
        QShortcut(QKeySequence("Ctrl+Shift+S"), self.main_window, self.main_window.file_operations.save_all_changes)
        QShortcut(QKeySequence("Ctrl+F"), self.main_window, self.main_window.dialog_manager.open_find_dialog)
        QShortcut(QKeySequence(Qt.Key.Key_F2), self.main_window, self.main_window.start_rename)
        QShortcut(QKeySequence("Alt+Right"), self.main_window, self.main_window.navigate_files_forward)
        QShortcut(QKeySequence("Alt+Left"), self.main_window, self.main_window.navigate_files_backward)
        QShortcut(QKeySequence("Alt+End"), self.main_window, self.main_window.select_last_item)
        QShortcut(QKeySequence("Alt+Home"), self.main_window, self.main_window.select_first_item)
        QShortcut(QKeySequence("Alt+PgUp"), self.main_window, lambda: self.main_window.navigate_files(-10))
        QShortcut(QKeySequence("Alt+PgDown"), self.main_window, lambda: self.main_window.navigate_files(10))
