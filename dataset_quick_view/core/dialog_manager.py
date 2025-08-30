from PyQt6.QtWidgets import QFileDialog, QMessageBox, QDialog
from ..tools.find_replace_dialog import FindReplaceDialog
from ..tools.prefix_suffix_dialog import PrefixSuffixDialog
from ..tools.clear_whitespace_dialog import ClearWhitespaceDialog
from ..tools.settings_dialog import SettingsDialog
from ..widgets.media_viewer import MediaViewer

class DialogManager:
    def __init__(self, main_window):
        self.main_window = main_window
        self.find_dialog = None

    def open_folder_dialog(self):
        new_folder_path = QFileDialog.getExistingDirectory(self.main_window, "Select Folder", self.main_window.app_state.folder_path)
        if new_folder_path and new_folder_path != self.main_window.app_state.folder_path:
            self.main_window.file_operations.load_new_folder(new_folder_path)

    def open_find_dialog(self):
        if self.find_dialog is None:
            self.find_dialog = FindReplaceDialog(self.main_window)
        self.find_dialog.show()
        self.find_dialog.activateWindow()

    def open_prefix_suffix_dialog(self):
        dialog = PrefixSuffixDialog(self.main_window)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.main_window.config.load_or_create_config() # Reload config after settings are saved
            self.main_window.settings_manager.load_settings() # Apply updated settings to UI

    def open_clear_whitespace_dialog(self):
        dialog = ClearWhitespaceDialog(self.main_window)
        dialog.exec()

    def open_settings_dialog(self):
        dialog = SettingsDialog(self.main_window.config, self.main_window)
        if dialog.exec():
            self.main_window.apply_layout_settings()
            self.main_window.file_list.apply_view_settings() # Apply new view mode
            reply = QMessageBox.question(self.main_window, 'Reload Dataset',
                                       "Media format settings have changed. Do you want to reload the dataset to apply them now?",
                                       QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                       QMessageBox.StandardButton.Yes)
            if reply == QMessageBox.StandardButton.Yes:
                self.main_window.file_operations.refresh_dataset()

    def open_detached_viewer(self):
        if not self.main_window.app_state.detached_viewer:
            self.main_window.app_state.detached_viewer = MediaViewer(self.main_window.config)
            self.main_window.app_state.detached_viewer.setWindowTitle("Detached Media Viewer")
            self.main_window.app_state.detached_viewer.resize(800, 600)
            current_item = self.main_window.file_list.currentItem()
            if current_item:
                media_path = current_item.data(Qt.ItemDataRole.UserRole)
                self.main_window.app_state.detached_viewer.set_media(media_path)
            self.main_window.app_state.detached_viewer.show()
        else:
            self.main_window.app_state.detached_viewer.activateWindow()

    def show_help_dialog(self):
        help_text = """<b>DatasetQuickView Help</b>
            <br><br>
            <b>Navigation:</b>
            <ul>
                <li><b>Alt + Right/Left:</b> Next/Previous item</li>
                <li><b>Alt + Home/End:</b> First/Last item</li>
                <li><b>Alt + PgUp/PgDown:</b> Jump 10 items</li>
            </ul>
            <br>
            <b>Editing & Saving:</b>
            <ul>
                <li>Text edits are cached in memory. Unsaved files are marked with an <i>*</i> and a color change.</li>
                <li><b>Auto-save:</b> If checked, saves changes for an item when you navigate away from it.</li>
                <li><b>Save:</b> Saves changes for the current item (Ctrl+S).</li>
                <li><b>Save All:</b> Saves all changes for all items (Ctrl+Shift+S).</li>
                <li>You will be prompted to save any unsaved work when closing the app or loading a new folder.</li>
            </ul>
            <br>
            <b>Tools:</b>
            <ul>
                <li><b>Load Folder:</b> Opens a new dataset folder.</li>
                <li><b>Find / Replace:</b> Find and replace text (Ctrl+F).</li>
                <li><b>Add Prefix/Suffix:</b> Add text to the beginning or end of text files.</li>
                <li><b>Detach Viewer:</b> Opens the media viewer in a separate window.</li>
            </ul>
            <br>
            <b>Settings:</b>
            <ul>
                <li><b>Recursive:</b> If checked, files will be loaded from sub-directories as well.</li>
                <li><b>Remember last folder:</b> Opens the last used folder on startup.</li>
                <li><b>Ctrl + Mouse Scroll (over text editor):</b> Adjust font size.</li>
                <li><b>Ctrl + Mouse Scroll (over file list in thumbnail mode):</b> Adjust thumbnail size.</li>
            </ul>"""
        QMessageBox.information(self.main_window, "Help - DatasetQuickView", help_text)
