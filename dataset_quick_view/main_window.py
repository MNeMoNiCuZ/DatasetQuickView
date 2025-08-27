from PyQt6.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QSplitter, QToolBar, QCheckBox, QSizePolicy, QPushButton, QFrame, QMessageBox, QFileDialog, QLabel, QListWidget, QTextEdit, QDialog, QLineEdit, QStackedWidget, QStyle
from PyQt6.QtGui import QShortcut, QKeySequence, QFont, QIcon, QAction
from PyQt6.QtCore import Qt, QEvent, pyqtSignal
import os, sys, subprocess

from .utils.file_handler import find_dataset_files
from .utils.config_manager import ConfigManager
from .widgets.file_list_view import FileListView
from .widgets.media_viewer import MediaViewer
from .widgets.text_editor_panel import TextEditorPanel
from .tools.find_replace_dialog import FindReplaceDialog
from .tools.prefix_suffix_dialog import PrefixSuffixDialog
from .tools.settings_dialog import SettingsDialog

class MainWindow(QMainWindow):
    file_loaded = pyqtSignal()

    def __init__(self, folder_path, config):
        super().__init__()
        self.folder_path = folder_path
        self.config = config
        self.detached_viewer = None
        self.current_font_size = int(self.config.get_setting('Display', 'font_size'))

        self.text_cache = {}
        self.dirty_files = set()

        self.setWindowTitle(f"DatasetQuickView - {self.folder_path}")
        self.resize(1200, 800)
        
        if getattr(sys, 'frozen', False):
            # Running in a PyInstaller bundle
            icon_path = os.path.join(sys._MEIPASS, 'DatasetQuickView_ICON.ico')
        else:
            # Running in a normal Python environment
            icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'DatasetQuickView_ICON.ico')
        self.setWindowIcon(QIcon(icon_path))

        # --- Corrected Initialization Order ---
        # 1. Create the UI
        self.setup_ui()
        # 2. Load settings from config and apply them to the UI
        self.load_settings()
        # 3. Connect signals after UI is created
        self.connect_signals()
        # 4. Now, load the initial dataset using the correct state of the checkbox
        self.dataset = find_dataset_files(self.folder_path, self.recursive_checkbox.isChecked())
        if not self.dataset:
            self.statusBar().showMessage("No media files found in the specified folder.", 5000)
        
        # 5. Populate the UI with data
        self.file_list.dataset = self.dataset
        self.file_list.populate_list(self.dataset.keys())
        
        # 6. Finish setup
        self.setup_hotkeys()
        self.apply_font_settings()
        self.center_on_screen()

        if self.dataset:
            self.file_list.setCurrentRow(0)

    def setup_ui(self):
        toolbar = QToolBar("Main Toolbar")
        toolbar.setMovable(False)
        toolbar.setStyleSheet("QToolBar { padding: 10px; }")
        self.addToolBar(toolbar)

        load_folder_button = QPushButton("Load Folder")
        load_folder_button.setToolTip("Open a different dataset folder.")
        load_folder_button.setStyleSheet("padding: 4px 8px;")
        load_folder_button.clicked.connect(self.open_folder_dialog)
        toolbar.addWidget(load_folder_button)

        self.remember_folder_checkbox = QCheckBox("Remember Folder")
        self.remember_folder_checkbox.setToolTip("Automatically load this folder the next time you open the application.")
        toolbar.addWidget(self.remember_folder_checkbox)

        self.recursive_checkbox = QCheckBox("Recursive")
        self.recursive_checkbox.setToolTip("Search for media in sub-folders as well.")
        toolbar.addWidget(self.recursive_checkbox)

        refresh_button = QPushButton("")
        refresh_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_BrowserReload))
        refresh_button.setToolTip("Refresh the current dataset.")
        refresh_button.setStyleSheet("padding: 4px 8px;")
        refresh_button.clicked.connect(self.refresh_dataset)
        toolbar.addWidget(refresh_button)

        open_file_dir_button = QPushButton("Open Folder")
        open_file_dir_button.setToolTip("Open the directory containing the selected file.")
        open_file_dir_button.setStyleSheet("padding: 4px 8px;")
        open_file_dir_button.clicked.connect(self.open_selected_file_directory)
        toolbar.addWidget(open_file_dir_button)

        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        toolbar.addWidget(spacer)

        detach_button = QPushButton("Detach Viewer")
        detach_button.setToolTip("Open the media viewer in a separate, resizable window.")
        detach_button.setStyleSheet("padding: 4px 8px;")
        detach_button.clicked.connect(self.open_detached_viewer)
        toolbar.addWidget(detach_button)

        settings_button = QPushButton("Settings")
        settings_button.setToolTip("Open the application settings.")
        settings_button.setStyleSheet("padding: 4px 8px;")
        settings_button.clicked.connect(self.open_settings_dialog)
        toolbar.addWidget(settings_button)

        help_button = QPushButton("?")
        help_button.setToolTip("Show the help dialog.")
        help_button.setStyleSheet("QPushButton { border-radius: 12px; font-weight: bold; font-size: 14px; width: 24px; height: 24px; } ")
        help_button.clicked.connect(self.show_help_dialog)
        toolbar.addWidget(help_button)

        main_container = QWidget()
        self.setCentralWidget(main_container)
        main_layout = QVBoxLayout(main_container)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)

        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        main_layout.addWidget(line)

        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(self.main_splitter)

        # Container for media viewer
        media_viewer_container = QWidget()
        media_viewer_layout = QVBoxLayout(media_viewer_container)
        media_viewer_layout.setContentsMargins(0,0,0,0)
        media_viewer_layout.setSpacing(0)

        # Filename display
        self.filename_stack = QStackedWidget()
        self.filename_stack.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        self.filename_stack.setFixedHeight(40) # Set a fixed height
        media_viewer_layout.addWidget(self.filename_stack)

        # Display widget (icon + label)
        self.filename_display_widget = QWidget()
        filename_layout = QHBoxLayout(self.filename_display_widget)
        filename_layout.setContentsMargins(0, 0, 0, 0)
        filename_layout.setSpacing(5)
        filename_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.edit_icon_label = QLabel("✎")
        self.edit_icon_label.setStyleSheet("font-size: 16px; color: white;")
        self.edit_icon_label.setToolTip("Rename file (Double-click name to edit)")
        self.edit_icon_label.setCursor(Qt.CursorShape.PointingHandCursor)
        self.edit_icon_label.installEventFilter(self)
        filename_layout.addWidget(self.edit_icon_label)

        self.filename_label = QLabel("")
        self.filename_label.setTextFormat(Qt.TextFormat.RichText)
        self.filename_label.setStyleSheet("font-size: 16px; padding: 5px; color: white;")
        self.filename_label.installEventFilter(self)
        filename_layout.addWidget(self.filename_label)
        
        self.filename_stack.addWidget(self.filename_display_widget)

        # Edit widget
        self.filename_edit = QLineEdit()
        self.filename_edit.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.filename_edit.setStyleSheet("font-size: 16px; padding: 5px; color: white; border: 1px solid white;")
        self.filename_edit.installEventFilter(self)
        self.filename_stack.addWidget(self.filename_edit)

        # Create with an empty dataset first
        self.file_list = FileListView(self.config, {})
        self.media_viewer = MediaViewer(self.config)
        self.media_viewer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        media_viewer_layout.addWidget(self.media_viewer)
        
        # --- Text Editor Panel with Toolbar ---
        text_panel_container = QWidget()
        text_panel_layout = QVBoxLayout(text_panel_container)
        text_panel_layout.setContentsMargins(0,0,0,0)
        text_panel_layout.setSpacing(0)

        text_toolbar = QToolBar("Text Toolbar")
        text_toolbar.setMovable(False)
        text_toolbar.setStyleSheet("""QToolBar { padding: 5px; }
        QToolButton#qt_toolbar_ext_button {
            background-color: #c0c0c0;
            border: 1px solid #888888;
            border-radius: 3px;
            padding: 5px;
        }""")
        
        self.auto_save_checkbox = QCheckBox("Auto-save")
        self.auto_save_checkbox.setToolTip("Automatically save changes when you move to a new item. If unchecked, you must save manually.")
        text_toolbar.addWidget(self.auto_save_checkbox)

        save_current_button = QPushButton("Save")
        save_current_button.setToolTip("Save any changes for the currently selected item (Ctrl+S).")
        save_current_button.setStyleSheet("padding: 4px 8px;")
        save_current_button.clicked.connect(self.save_current_item_changes)
        text_toolbar.addWidget(save_current_button)

        save_all_button = QPushButton("Save All")
        save_all_button.setToolTip("Save all unsaved changes across all items (Ctrl+Shift+S).")
        save_all_button.setStyleSheet("padding: 4px 8px;")
        save_all_button.clicked.connect(self.save_all_changes)
        text_toolbar.addWidget(save_all_button)

        revert_button = QPushButton("Revert")
        revert_button.setToolTip("Revert all unsaved changes for the current item.")
        revert_button.setStyleSheet("padding: 4px 8px;")
        revert_button.clicked.connect(self.revert_current_item_changes)
        text_toolbar.addWidget(revert_button)

        revert_all_button = QPushButton("Revert All")
        revert_all_button.setToolTip("Revert all unsaved changes across all items.")
        revert_all_button.setStyleSheet("padding: 4px 8px;")
        revert_all_button.clicked.connect(self.revert_all_changes)
        text_toolbar.addWidget(revert_all_button)
        
        text_toolbar.addSeparator()

        find_replace_button = QPushButton("Find / Replace")
        find_replace_button.setToolTip("Find and replace text across the dataset (Ctrl+F).")
        find_replace_button.setStyleSheet("padding: 4px 8px;")
        find_replace_button.clicked.connect(self.open_find_dialog)
        text_toolbar.addWidget(find_replace_button)

        prefix_suffix_button = QPushButton("Add Prefix/Suffix")
        prefix_suffix_button.setToolTip("Add text to the beginning or end of the text files for multiple items.")
        prefix_suffix_button.setStyleSheet("padding: 4px 8px;")
        prefix_suffix_button.clicked.connect(self.open_prefix_suffix_dialog)
        text_toolbar.addWidget(prefix_suffix_button)
        
        text_panel_layout.addWidget(text_toolbar)

        self.text_editor_panel = TextEditorPanel(self)
        text_panel_layout.addWidget(self.text_editor_panel)
        # --- End Text Editor Panel with Toolbar ---


        self.file_list.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        media_viewer_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        text_panel_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self.main_splitter.addWidget(self.file_list)
        self.main_splitter.addWidget(media_viewer_container)
        self.main_splitter.addWidget(text_panel_container)
        self.apply_layout_settings()

    def connect_signals(self):
        self.file_list.currentItemChanged.connect(self.on_file_selected)
        self.text_editor_panel.text_modified.connect(self.on_text_modified)
        self.recursive_checkbox.toggled.connect(self.update_status) # Update title when toggled
        self.file_list.list_widget.viewport().installEventFilter(self)
        self.filename_edit.returnPressed.connect(self.commit_rename)

    def setup_hotkeys(self):
        QShortcut(QKeySequence("Ctrl+S"), self, self.save_current_item_changes)
        QShortcut(QKeySequence("Ctrl+Shift+S"), self, self.save_all_changes)
        QShortcut(QKeySequence("Ctrl+F"), self, self.open_find_dialog)
        QShortcut(QKeySequence(Qt.Key.Key_F2), self, self.start_rename)
        QShortcut(QKeySequence("Alt+Right"), self, lambda: self.navigate_files(1))
        QShortcut(QKeySequence("Alt+Left"), self, lambda: self.navigate_files(-1))
        QShortcut(QKeySequence("Alt+End"), self, self.select_last_item)
        QShortcut(QKeySequence("Alt+Home"), self, self.select_first_item)
        QShortcut(QKeySequence("Alt+PgUp"), self, lambda: self.navigate_files(-10))
        QShortcut(QKeySequence("Alt+PgDown"), self, lambda: self.navigate_files(10))

    def load_settings(self):
        self.auto_save_checkbox.setChecked(self.config.get_bool_setting('Editing', 'auto_save'))
        self.remember_folder_checkbox.setChecked(self.config.get_bool_setting('General', 'remember_last_folder'))
        self.recursive_checkbox.setChecked(self.config.get_bool_setting('General', 'recursive_search'))

    def save_settings(self):
        self.config.set_setting('Editing', 'auto_save', str(self.auto_save_checkbox.isChecked()))
        self.config.set_setting('General', 'remember_last_folder', str(self.remember_folder_checkbox.isChecked()))
        self.config.set_setting('General', 'recursive_search', str(self.recursive_checkbox.isChecked()))
        self.config.set_setting('Display', 'font_size', str(self.current_font_size))
        if self.remember_folder_checkbox.isChecked():
            self.config.set_setting('General', 'last_folder_path', self.folder_path)
        self.config.save_config()

    def on_file_selected(self, current_item, previous_item):
        if self.filename_stack.currentWidget() == self.filename_edit:
            self.cancel_rename()
        if previous_item is not None and self.auto_save_checkbox.isChecked():
            self.save_item_changes(previous_item.data(Qt.ItemDataRole.UserRole))

        if current_item is None:
            self.media_viewer.clear_media()
            self.text_editor_panel.load_text_files([], self.current_font_size, self.text_cache)
            self.filename_label.setText("") # Clear filename label
            return

        media_path = current_item.data(Qt.ItemDataRole.UserRole)
        text_paths = self.dataset.get(media_path, [])

        # If no text files are associated, create a placeholder for a new .txt file
        if not text_paths:
            basename, _ = os.path.splitext(media_path)
            new_txt_path = basename + ".txt"
            text_paths = [new_txt_path]
        
        self.media_viewer.set_media(media_path)
        self.text_editor_panel.load_text_files(text_paths, self.current_font_size, self.text_cache)

        # Update filename label
        base_name = os.path.basename(media_path)
        name, ext = os.path.splitext(base_name)
        self.filename_label.setText(f"<b>{name}</b>{ext}")

        if text_paths:
            self.text_editor_panel.focus_and_move_cursor_to_end(text_paths[0])

        if hasattr(self, 'find_dialog') and self.find_dialog and self.find_dialog.isVisible():
            self.find_dialog.sync_to_media_item(media_path)
        
        if self.detached_viewer:
            self.detached_viewer.set_media(media_path)
        self.update_status()
        self.file_loaded.emit()

    def on_text_modified(self, text_path, new_content):
        self.text_cache[text_path] = new_content
        if text_path not in self.dirty_files:
            self.dirty_files.add(text_path)
            media_path = self.file_list.get_media_path_from_text_path(text_path)
            if media_path:
                self.file_list.set_item_dirty(media_path, True)

    def save_item_changes(self, media_path):
        if not media_path: return
        
        saved_count = 0
        # Create a copy of the dirty_files set to iterate over, as it will be modified
        for dirty_path in list(self.dirty_files):
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
                        f.write(self.text_cache[dirty_path])
                    self.dirty_files.remove(dirty_path)
                    saved_count += 1
                except Exception as e:
                    self.statusBar().showMessage(f"Error saving {dirty_path}: {e}", 5000)
        
        if saved_count > 0:
            # Check if any other dirty files for this media_path remain
            has_remaining_dirty_files_for_item = False
            for dirty_path in self.dirty_files:
                dirty_dir = os.path.dirname(dirty_path)
                dirty_basename_no_ext = os.path.splitext(os.path.basename(dirty_path))[0]
                media_dir = os.path.dirname(media_path)
                media_basename_no_ext = os.path.splitext(os.path.basename(media_path))[0]
                if media_dir == dirty_dir and media_basename_no_ext == dirty_basename_no_ext:
                    has_remaining_dirty_files_for_item = True
                    break
            self.file_list.set_item_dirty(media_path, has_remaining_dirty_files_for_item)
            self.statusBar().showMessage(f"Saved {saved_count} file(s) for current item.", 2000)

    def save_current_item_changes(self):
        current_item = self.file_list.currentItem()
        if current_item:
            media_path = current_item.data(Qt.ItemDataRole.UserRole)
            self.save_item_changes(media_path)

    def save_all_changes(self):
        num_saved = 0
        # Create a copy of the set to iterate over, as it might be modified
        for path in list(self.dirty_files):
            try:
                os.makedirs(os.path.dirname(path), exist_ok=True)
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(self.text_cache[path])
                self.dirty_files.remove(path)
                
                # Update the visual indicator in the file list
                # Check if this media_path still has any dirty files associated with it
                media_path = self.file_list.get_media_path_from_text_path(path)
                if media_path:
                    has_remaining_dirty_files_for_item = False
                    for dirty_file_path in self.dirty_files:
                        dirty_media_path = self.file_list.get_media_path_from_text_path(dirty_file_path)
                        if dirty_media_path == media_path:
                            has_remaining_dirty_files_for_item = True
                            break
                    self.file_list.set_item_dirty(media_path, has_remaining_dirty_files_for_item)
                num_saved += 1
            except Exception as e:
                self.statusBar().showMessage(f"Error saving {path}: {e}", 5000)
        if num_saved > 0:
            self.statusBar().showMessage(f"Saved {num_saved} file(s).", 2000)

    def revert_current_item_changes(self):
        current_item = self.file_list.currentItem()
        if not current_item:
            return

        media_path = current_item.data(Qt.ItemDataRole.UserRole)
        text_paths = self.dataset.get(media_path, [])
        
        if not text_paths:
            basename, _ = os.path.splitext(media_path)
            new_txt_path = basename + ".txt"
            text_paths = [new_txt_path]

        reverted_count = 0
        for text_path in text_paths:
            if text_path in self.dirty_files:
                self.dirty_files.remove(text_path)
                if text_path in self.text_cache:
                    del self.text_cache[text_path]
                reverted_count += 1
        
        if reverted_count > 0:
            self.file_list.set_item_dirty(media_path, False)
            self.on_file_selected(current_item, None) # Reload the view for the current item
            self.statusBar().showMessage(f"Reverted changes for {reverted_count} file(s).", 2000)

    def revert_all_changes(self):
        if not self.dirty_files:
            return

        reply = QMessageBox.question(self, 'Revert All Changes',
                                   "Are you sure you want to revert all unsaved changes?",
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                   QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            reverted_count = len(self.dirty_files)
            self.dirty_files.clear()
            self.text_cache.clear()

            for i in range(self.file_list.count()):
                item = self.file_list.list_widget.item(i)
                media_path = item.data(Qt.ItemDataRole.UserRole)
                self.file_list.set_item_dirty(media_path, False)

            # Reload the current item to refresh the display
            current_item = self.file_list.currentItem()
            if current_item:
                self.on_file_selected(current_item, None)

            self.statusBar().showMessage(f"Reverted changes for {reverted_count} file(s).", 2000)

    def update_status(self):
        current = self.file_list.currentRow()
        total = self.file_list.count()
        title = f"({current + 1} / {total}) - DatasetQuickView - {self.folder_path}"
        if self.recursive_checkbox.isChecked():
            title += " (Recursive)"
        self.setWindowTitle(title)
        self.file_list.update_progress(current, total)

    def apply_font_settings(self):
        font = QFont()
        font.setPointSize(self.current_font_size)
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
                    self.current_font_size += 1
                else:
                    self.current_font_size = max(6, self.current_font_size - 1)
                self.apply_font_settings()
                self.config.set_setting('Display', 'font_size', str(self.current_font_size))
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

    def commit_rename(self):
        current_item = self.file_list.currentItem()
        if not current_item:
            self.cancel_rename()
            return

        old_media_path = current_item.data(Qt.ItemDataRole.UserRole)
        directory = os.path.dirname(old_media_path)
        _, ext = os.path.splitext(old_media_path)
        
        new_name = self.filename_edit.text()
        if not new_name or new_name.isspace():
            QMessageBox.warning(self, "Invalid Name", "Filename cannot be empty.")
            self.cancel_rename()
            return

        new_media_path = os.path.join(directory, new_name + ext)

        if old_media_path == new_media_path:
            self.cancel_rename()
            return

        if os.path.exists(new_media_path):
            QMessageBox.warning(self, "Rename Failed", f"A file named '{os.path.basename(new_media_path)}' already exists.")
            return

        try:
            # Rename media file
            os.rename(old_media_path, new_media_path)

            # Rename associated text files
            old_text_paths = self.dataset.get(old_media_path, [])
            new_text_paths = []
            for old_text_path in old_text_paths:
                _, text_ext = os.path.splitext(old_text_path)
                new_text_path = os.path.join(directory, new_name + text_ext)
                if os.path.exists(old_text_path):
                    os.rename(old_text_path, new_text_path)
                new_text_paths.append(new_text_path)

            # Update dataset
            self.dataset[new_media_path] = new_text_paths
            del self.dataset[old_media_path]

            # Update file list
            self.file_list.rename_media_file(old_media_path, new_media_path)

            # Update UI
            self.filename_label.setText(f"<b>{new_name}</b>{ext}")
            self.cancel_rename()
            self.statusBar().showMessage(f"Renamed to {new_name}{ext}", 3000)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not rename file: {e}")
            # Attempt to revert changes if something went wrong
            if os.path.exists(new_media_path) and not os.path.exists(old_media_path):
                os.rename(new_media_path, old_media_path)
            self.cancel_rename()

    def closeEvent(self, event):
        if self.dirty_files:
            reply = QMessageBox.question(self, 'Unsaved Changes',
                                       "You have unsaved changes. Do you want to save them before exiting?",
                                       QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel,
                                       QMessageBox.StandardButton.Cancel)

            if reply == QMessageBox.StandardButton.Save:
                self.save_all_changes()
                event.accept()
            elif reply == QMessageBox.StandardButton.Discard:
                event.accept()
            else:
                event.ignore()
                return
        
        if self.detached_viewer:
            self.detached_viewer.close()
        self.save_settings()
        super().closeEvent(event)

    def center_on_screen(self):
        screen_geo = self.screen().availableGeometry()
        self.move(screen_geo.center() - self.frameGeometry().center())

    def open_folder_dialog(self):
        new_folder_path = QFileDialog.getExistingDirectory(self, "Select Folder", self.folder_path)
        if new_folder_path and new_folder_path != self.folder_path:
            self.load_new_folder(new_folder_path)

    def load_new_folder(self, folder_path):
        if self.dirty_files:
            reply = QMessageBox.question(self, 'Unsaved Changes',
                                       "You have unsaved changes in the current folder. Save them before loading a new one?",
                                       QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel,
                                       QMessageBox.StandardButton.Cancel)

            if reply == QMessageBox.StandardButton.Save:
                self.save_all_changes()
            elif reply == QMessageBox.StandardButton.Cancel:
                return

        self.folder_path = folder_path
        self.text_cache = {}
        self.dirty_files = set()
        self.dataset = find_dataset_files(self.folder_path, self.recursive_checkbox.isChecked())

        if not self.dataset:
            self.statusBar().showMessage(f"No media files found in {folder_path}.", 5000)
            self.file_list.list_widget.clear()
            self.file_list.update_progress(0, 0)
            self.text_editor_panel.load_text_files([], self.current_font_size, self.text_cache)
            self.media_viewer.clear_media()
        else:
            self.file_list.dataset = self.dataset
            self.file_list.populate_list(self.dataset.keys())
            self.file_list.setCurrentRow(0)

        self.setWindowTitle(f"DatasetQuickView - {self.folder_path}")

    def refresh_dataset(self):
        if self.dirty_files:
            reply = QMessageBox.question(self, 'Unsaved Changes',
                                       "You have unsaved changes. Do you want to save them before refreshing?",
                                       QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel,
                                       QMessageBox.StandardButton.Cancel)

            if reply == QMessageBox.StandardButton.Save:
                self.save_all_changes()
            elif reply == QMessageBox.StandardButton.Cancel:
                return

        self.text_cache = {}
        self.dirty_files = set()
        self.dataset = find_dataset_files(self.folder_path, self.recursive_checkbox.isChecked())

        if not self.dataset:
            self.statusBar().showMessage(f"No media files found in {self.folder_path}.", 5000)
            self.file_list.list_widget.clear()
            self.file_list.update_progress(0, 0)
            self.text_editor_panel.load_text_files([], self.current_font_size, self.text_cache)
            self.media_viewer.clear_media()
        else:
            self.file_list.dataset = self.dataset
            self.file_list.populate_list(self.dataset.keys())
            self.file_list.setCurrentRow(0)
        self.update_status()

    def open_find_dialog(self):
        if not hasattr(self, 'find_dialog') or self.find_dialog is None:
            self.find_dialog = FindReplaceDialog(self)
        self.find_dialog.show()
        self.find_dialog.activateWindow()

    def open_prefix_suffix_dialog(self):
        dialog = PrefixSuffixDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.config.load_or_create_config() # Reload config after settings are saved
            self.load_settings() # Apply updated settings to UI

    def open_settings_dialog(self):
        dialog = SettingsDialog(self.config, self)
        if dialog.exec():
            self.apply_layout_settings()
            self.file_list.apply_view_settings() # Apply new view mode
            reply = QMessageBox.question(self, 'Reload Dataset',
                                       "Media format settings have changed. Do you want to reload the dataset to apply them now?",
                                       QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                       QMessageBox.StandardButton.Yes)
            if reply == QMessageBox.StandardButton.Yes:
                self.load_new_folder(self.folder_path)

    def open_detached_viewer(self):
        if not self.detached_viewer:
            self.detached_viewer = MediaViewer(self.config)
            self.detached_viewer.setWindowTitle("Detached Media Viewer")
            self.detached_viewer.resize(800, 600)
            current_item = self.file_list.currentItem()
            if current_item:
                media_path = current_item.data(Qt.ItemDataRole.UserRole)
                self.detached_viewer.set_media(media_path)
            self.detached_viewer.show()
        else:
            self.detached_viewer.activateWindow()

    def navigate_files(self, delta):
        current_row = self.file_list.currentRow()
        new_row = current_row + delta
        new_row = max(0, min(self.file_list.count() - 1, new_row))
        self.file_list.setCurrentRow(new_row)

    def select_first_item(self):
        self.file_list.setCurrentRow(0)

    def select_last_item(self):
        self.file_list.setCurrentRow(self.file_list.count() - 1)

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
        QMessageBox.information(self, "Help - DatasetQuickView", help_text)

    def open_selected_file_directory(self):
        current_item = self.file_list.currentItem()
        if not current_item:
            self.statusBar().showMessage("No file selected.", 3000)
            return

        media_path = current_item.data(Qt.ItemDataRole.UserRole)

        try:
            if sys.platform == "win32":
                import ctypes
                from ctypes import wintypes
                
                normalized_path = os.path.normpath(media_path)
                
                class ITEMIDLIST(ctypes.Structure):
                    pass
                
                ctypes.windll.shell32.ILCreateFromPathW.argtypes = [wintypes.LPCWSTR]
                ctypes.windll.shell32.ILCreateFromPathW.restype = ctypes.POINTER(ITEMIDLIST)
                
                ctypes.windll.shell32.SHOpenFolderAndSelectItems.argtypes = [
                    ctypes.POINTER(ITEMIDLIST),
                    wintypes.UINT,
                    ctypes.POINTER(ctypes.POINTER(ITEMIDLIST)),
                    wintypes.DWORD
                ]
                
                pidl = ctypes.windll.shell32.ILCreateFromPathW(normalized_path)
                if pidl:
                    try:
                        ctypes.windll.shell32.SHOpenFolderAndSelectItems(pidl, 0, None, 0)
                    finally:
                        ctypes.windll.shell32.ILFree(pidl)

            elif sys.platform == "darwin":
                subprocess.Popen(['open', '-R', media_path])
            else:
                directory = os.path.dirname(media_path)
                subprocess.Popen(['xdg-open', directory])
        except Exception as e:
            self.statusBar().showMessage(f"Error opening directory: {e}", 5000)
