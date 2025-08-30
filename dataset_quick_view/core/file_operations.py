import os
from PyQt6.QtWidgets import QMessageBox
from PyQt6.QtCore import Qt
from .app_state import AppState
from ..utils.file_handler import find_dataset_files

class FileOperations:
    def __init__(self, app_state, main_window):
        self.app_state = app_state
        self.main_window = main_window

    def load_dataset(self, recursive):
        self.app_state.dataset = find_dataset_files(self.app_state.folder_path, recursive)
        if not self.app_state.dataset:
            self.main_window.statusBar().showMessage("No media files found in the specified folder.", 5000)

    def save_item_changes(self, media_path):
        if not media_path: return
        
        saved_count = 0
        # Create a copy of the dirty_files set to iterate over, as it will be modified
        for dirty_path in list(self.app_state.dirty_files):
            # Check if this dirty_path belongs to the current media_path
            media_dir = os.path.dirname(media_path)
            media_basename_no_ext = os.path.splitext(os.path.basename(media_path))[0]

            dirty_dir = os.path.dirname(dirty_path)
            dirty_basename_no_ext = os.path.splitext(os.path.basename(dirty_path))[0]
            
            if media_dir == dirty_dir and media_basename_no_ext == dirty_basename_no_ext:
                try:
                    # Ensure directory exists for new files
                    os.makedirs(os.path.dirname(dirty_path), exist_ok=True)
                    with open(dirty_path, 'w', encoding='utf-8') as f:
                        f.write(self.app_state.text_cache[dirty_path])
                    self.app_state.dirty_files.remove(dirty_path)
                    saved_count += 1
                except Exception as e:
                    self.main_window.statusBar().showMessage(f"Error saving {dirty_path}: {e}", 5000)
        
        if saved_count > 0:
            # Check if any other dirty files for this media_path remain
            has_remaining_dirty_files_for_item = False
            for dirty_path in self.app_state.dirty_files:
                dirty_dir = os.path.dirname(dirty_path)
                dirty_basename_no_ext = os.path.splitext(os.path.basename(dirty_path))[0]
                media_dir = os.path.dirname(media_path)
                media_basename_no_ext = os.path.splitext(os.path.basename(media_path))[0]
                if media_dir == dirty_dir and media_basename_no_ext == dirty_basename_no_ext:
                    has_remaining_dirty_files_for_item = True
                    break
            self.main_window.file_list.set_item_dirty(media_path, has_remaining_dirty_files_for_item)
            self.main_window.statusBar().showMessage(f"Saved {saved_count} file(s) for current item.", 2000)

    def save_current_item_changes(self):
        current_item = self.main_window.file_list.currentItem()
        if current_item:
            media_path = current_item.data(Qt.ItemDataRole.UserRole)
            self.save_item_changes(media_path)

    def save_all_changes(self):
        num_saved = 0
        # Create a copy of the set to iterate over, as it might be modified
        for path in list(self.app_state.dirty_files):
            try:
                os.makedirs(os.path.dirname(path), exist_ok=True)
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(self.app_state.text_cache[path])
                self.app_state.dirty_files.remove(path)
                
                # Update the visual indicator in the file list
                # Check if this media_path still has any dirty files associated with it
                media_path = self.main_window.file_list.get_media_path_from_text_path(path)
                if media_path:
                    has_remaining_dirty_files_for_item = False
                    for dirty_file_path in self.app_state.dirty_files:
                        dirty_media_path = self.main_window.file_list.get_media_path_from_text_path(dirty_file_path)
                        if dirty_media_path == media_path:
                            has_remaining_dirty_files_for_item = True
                            break
                    self.main_window.file_list.set_item_dirty(media_path, has_remaining_dirty_files_for_item)
                num_saved += 1
            except Exception as e:
                self.main_window.statusBar().showMessage(f"Error saving {path}: {e}", 5000)
        if num_saved > 0:
            self.main_window.statusBar().showMessage(f"Saved {num_saved} file(s).", 2000)

    def revert_current_item_changes(self):
        current_item = self.main_window.file_list.currentItem()
        if not current_item:
            return

        media_path = current_item.data(Qt.ItemDataRole.UserRole)
        text_paths = self.app_state.dataset.get(media_path, [])
        
        if not text_paths:
            basename, _ = os.path.splitext(media_path)
            new_txt_path = basename + ".txt"
            text_paths = [new_txt_path]

        reverted_count = 0
        for text_path in text_paths:
            if text_path in self.app_state.dirty_files:
                self.app_state.dirty_files.remove(text_path)
                if text_path in self.app_state.text_cache:
                    del self.app_state.text_cache[text_path]
                reverted_count += 1
        
        if reverted_count > 0:
            self.main_window.file_list.set_item_dirty(media_path, False)
            self.main_window.on_file_selected(current_item, None) # Reload the view for the current item
            self.main_window.statusBar().showMessage(f"Reverted changes for {reverted_count} file(s).", 2000)

    def revert_all_changes(self):
        if not self.app_state.dirty_files:
            return

        reply = QMessageBox.question(self.main_window, 'Revert All Changes',
                                   "Are you sure you want to revert all unsaved changes?",
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                   QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            reverted_count = len(self.app_state.dirty_files)
            self.app_state.dirty_files.clear()
            self.app_state.text_cache.clear()

            for i in range(self.main_window.file_list.count()):
                item = self.main_window.file_list.list_widget.item(i)
                media_path = item.data(Qt.ItemDataRole.UserRole)
                self.main_window.file_list.set_item_dirty(media_path, False)

            # Reload the current item to refresh the display
            current_item = self.main_window.file_list.currentItem()
            if current_item:
                self.main_window.on_file_selected(current_item, None)

            self.main_window.statusBar().showMessage(f"Reverted changes for {reverted_count} file(s).", 2000)

    def refresh_dataset(self):
        if self.app_state.dirty_files:
            reply = QMessageBox.question(self.main_window, 'Unsaved Changes',
                                       "You have unsaved changes. Do you want to save them before refreshing?",
                                       QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel,
                                       QMessageBox.StandardButton.Cancel)

            if reply == QMessageBox.StandardButton.Save:
                self.save_all_changes()
            elif reply == QMessageBox.StandardButton.Cancel:
                return

        self.app_state.text_cache = {}
        self.app_state.dirty_files = set()
        self.load_dataset(self.main_window.recursive_checkbox.isChecked())

        if not self.app_state.dataset:
            self.main_window.statusBar().showMessage(f"No media files found in {self.app_state.folder_path}.", 5000)
            self.main_window.file_list.list_widget.clear()
            self.main_window.file_list.update_progress(0, 0)
            self.main_window.text_editor_panel.load_text_files([], self.app_state.current_font_size, self.app_state.text_cache)
            self.main_window.media_viewer.clear_media()
        else:
            self.main_window.file_list.dataset = self.app_state.dataset
            self.main_window.file_list.populate_list(self.app_state.dataset.keys())
            self.main_window.file_list.setCurrentRow(0)
        self.main_window.update_status()

    def commit_rename(self, new_name):
        current_item = self.main_window.file_list.currentItem()
        if not current_item:
            self.main_window.cancel_rename()
            return

        old_media_path = current_item.data(Qt.ItemDataRole.UserRole)
        directory = os.path.dirname(old_media_path)
        _, ext = os.path.splitext(old_media_path)
        
        if not new_name or new_name.isspace():
            QMessageBox.warning(self.main_window, "Invalid Name", "Filename cannot be empty.")
            self.main_window.cancel_rename()
            return

        new_media_path = os.path.join(directory, new_name + ext)

        if old_media_path == new_media_path:
            self.main_window.cancel_rename()
            return

        if os.path.exists(new_media_path):
            QMessageBox.warning(self.main_window, "Rename Failed", f"A file named '{os.path.basename(new_media_path)}' already exists.")
            return

        try:
            os.rename(old_media_path, new_media_path)

            old_text_paths = self.app_state.dataset.get(old_media_path, [])
            new_text_paths = []
            for old_text_path in old_text_paths:
                _, text_ext = os.path.splitext(old_text_path)
                new_text_path = os.path.join(directory, new_name + text_ext)
                if os.path.exists(old_text_path):
                    os.rename(old_text_path, new_text_path)
                new_text_paths.append(new_text_path)

            self.app_state.dataset[new_media_path] = new_text_paths
            del self.app_state.dataset[old_media_path]

            self.main_window.file_list.rename_media_file(old_media_path, new_media_path)

            self.main_window.filename_label.setText(f"<b>{new_name}</b>{ext}")
            self.main_window.cancel_rename()
            self.main_window.statusBar().showMessage(f"Renamed to {new_name}{ext}", 3000)

        except Exception as e:
            QMessageBox.critical(self.main_window, "Error", f"Could not rename file: {e}")
            if os.path.exists(new_media_path) and not os.path.exists(old_media_path):
                os.rename(new_media_path, old_media_path)
            self.main_window.cancel_rename()

    def load_new_folder(self, folder_path):
        if self.app_state.dirty_files:
            reply = QMessageBox.question(self.main_window, 'Unsaved Changes',
                                       "You have unsaved changes in the current folder. Save them before loading a new one?",
                                       QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel,
                                       QMessageBox.StandardButton.Cancel)

            if reply == QMessageBox.StandardButton.Save:
                self.save_all_changes()
            elif reply == QMessageBox.StandardButton.Cancel:
                return

        self.app_state.folder_path = folder_path
        self.app_state.text_cache = {}
        self.app_state.dirty_files = set()
        self.load_dataset(self.main_window.recursive_checkbox.isChecked())

        if not self.app_state.dataset:
            self.main_window.statusBar().showMessage(f"No media files found in {folder_path}.", 5000)
            self.main_window.file_list.list_widget.clear()
            self.main_window.file_list.update_progress(0, 0)
            self.main_window.text_editor_panel.load_text_files([], self.app_state.current_font_size, self.app_state.text_cache)
            self.main_window.media_viewer.clear_media()
        else:
            self.main_window.file_list.dataset = self.app_state.dataset
            self.main_window.file_list.populate_list(self.app_state.dataset.keys())
            self.main_window.file_list.setCurrentRow(0)

        self.main_window.setWindowTitle(f"DatasetQuickView - {self.app_state.folder_path}")
