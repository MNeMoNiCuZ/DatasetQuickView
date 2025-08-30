from PyQt6.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QSplitter, QToolBar, QCheckBox, QSizePolicy, QPushButton, QFrame, QLabel, QLineEdit, QStackedWidget, QStyle
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import Qt

from ..widgets.file_list_view import FileListView
from ..widgets.media_viewer import MediaViewer
from ..widgets.text_editor_panel import TextEditorPanel

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        self.toolbar = QToolBar("Main Toolbar")
        self.toolbar.setMovable(False)
        self.toolbar.setStyleSheet("QToolBar { padding: 10px; }")
        MainWindow.addToolBar(self.toolbar)

        self.load_folder_button = QPushButton("Load Folder")
        self.load_folder_button.setToolTip("Open a different dataset folder.")
        self.load_folder_button.setStyleSheet("padding: 4px 8px;")
        self.toolbar.addWidget(self.load_folder_button)

        self.remember_folder_checkbox = QCheckBox("Remember Folder")
        self.remember_folder_checkbox.setToolTip("Automatically load this folder the next time you open the application.")
        self.toolbar.addWidget(self.remember_folder_checkbox)

        self.recursive_checkbox = QCheckBox("Recursive")
        self.recursive_checkbox.setToolTip("Search for media in sub-folders as well.")
        self.toolbar.addWidget(self.recursive_checkbox)

        self.refresh_button = QPushButton("")
        self.refresh_button.setIcon(MainWindow.style().standardIcon(QStyle.StandardPixmap.SP_BrowserReload))
        self.refresh_button.setToolTip("Refresh the current dataset.")
        self.refresh_button.setStyleSheet("padding: 4px 8px;")
        self.toolbar.addWidget(self.refresh_button)

        self.open_file_dir_button = QPushButton("Open Folder")
        self.open_file_dir_button.setToolTip("Open the directory containing the selected file.")
        self.open_file_dir_button.setStyleSheet("padding: 4px 8px;")
        self.toolbar.addWidget(self.open_file_dir_button)

        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.toolbar.addWidget(spacer)

        self.detach_button = QPushButton("Detach Viewer")
        self.detach_button.setToolTip("Open the media viewer in a separate, resizable window.")
        self.detach_button.setStyleSheet("padding: 4px 8px;")
        self.toolbar.addWidget(self.detach_button)

        self.settings_button = QPushButton("Settings")
        self.settings_button.setToolTip("Open the application settings.")
        self.settings_button.setStyleSheet("padding: 4px 8px;")
        self.toolbar.addWidget(self.settings_button)

        self.help_button = QPushButton("?")
        self.help_button.setToolTip("Show the help dialog.")
        self.help_button.setStyleSheet("QPushButton { border-radius: 12px; font-weight: bold; font-size: 14px; width: 24px; height: 24px; } ")
        self.toolbar.addWidget(self.help_button)

        self.main_container = QWidget()
        MainWindow.setCentralWidget(self.main_container)
        self.main_layout = QVBoxLayout(self.main_container)
        self.main_layout.setContentsMargins(5, 5, 5, 5)
        self.main_layout.setSpacing(5)

        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        self.main_layout.addWidget(line)

        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.main_layout.addWidget(self.main_splitter)

        # Container for media viewer
        self.media_viewer_container = QWidget()
        self.media_viewer_layout = QVBoxLayout(self.media_viewer_container)
        self.media_viewer_layout.setContentsMargins(0,0,0,0)
        self.media_viewer_layout.setSpacing(0)

        # Filename display
        self.filename_stack = QStackedWidget()
        self.filename_stack.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        self.filename_stack.setFixedHeight(40) # Set a fixed height
        self.media_viewer_layout.addWidget(self.filename_stack)

        # Display widget (icon + label)
        self.filename_display_widget = QWidget()
        self.filename_layout = QHBoxLayout(self.filename_display_widget)
        self.filename_layout.setContentsMargins(0, 0, 0, 0)
        self.filename_layout.setSpacing(5)
        self.filename_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.edit_icon_label = QLabel("✎")
        self.edit_icon_label.setStyleSheet("font-size: 16px; color: white;")
        self.edit_icon_label.setToolTip("Rename file (Double-click name to edit)")
        self.edit_icon_label.setCursor(Qt.CursorShape.PointingHandCursor)
        self.filename_layout.addWidget(self.edit_icon_label)

        self.filename_label = QLabel("")
        self.filename_label.setTextFormat(Qt.TextFormat.RichText)
        self.filename_label.setStyleSheet("font-size: 16px; padding: 5px; color: white;")
        self.filename_layout.addWidget(self.filename_label)
        
        self.filename_stack.addWidget(self.filename_display_widget)

        # Edit widget
        self.filename_edit = QLineEdit()
        self.filename_edit.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.filename_edit.setStyleSheet("font-size: 16px; padding: 5px; color: white; border: 1px solid white;")
        self.filename_stack.addWidget(self.filename_edit)

        # Create with an empty dataset first
        self.file_list = FileListView(MainWindow.config, {})
        self.media_viewer = MediaViewer(MainWindow.config)
        self.media_viewer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.media_viewer_layout.addWidget(self.media_viewer)
        
        # --- Text Editor Panel with Toolbar ---
        self.text_panel_container = QWidget()
        self.text_panel_layout = QVBoxLayout(self.text_panel_container)
        self.text_panel_layout.setContentsMargins(0,0,0,0)
        self.text_panel_layout.setSpacing(0)

        self.text_toolbar = QToolBar("Text Toolbar")
        self.text_toolbar.setMovable(False)
        self.text_toolbar.setStyleSheet("""QToolBar { padding: 5px; }
        QToolButton#qt_toolbar_ext_button {
            background-color: #c0c0c0;
            border: 1px solid #888888;
            border-radius: 3px;
            padding: 5px;
        }""")
        
        self.auto_save_checkbox = QCheckBox("Auto-save")
        self.auto_save_checkbox.setToolTip("Automatically save changes when you move to a new item. If unchecked, you must save manually.")
        self.text_toolbar.addWidget(self.auto_save_checkbox)

        self.save_current_button = QPushButton("Save")
        self.save_current_button.setToolTip("Save any changes for the currently selected item (Ctrl+S).")
        self.save_current_button.setStyleSheet("padding: 4px 8px;")
        self.text_toolbar.addWidget(self.save_current_button)

        self.save_all_button = QPushButton("Save All")
        self.save_all_button.setToolTip("Save all unsaved changes across all items (Ctrl+Shift+S).")
        self.save_all_button.setStyleSheet("padding: 4px 8px;")
        self.text_toolbar.addWidget(self.save_all_button)

        self.revert_button = QPushButton("Revert")
        self.revert_button.setToolTip("Revert all unsaved changes for the current item.")
        self.revert_button.setStyleSheet("padding: 4px 8px;")
        self.text_toolbar.addWidget(self.revert_button)

        self.revert_all_button = QPushButton("Revert All")
        self.revert_all_button.setToolTip("Revert all unsaved changes across all items.")
        self.revert_all_button.setStyleSheet("padding: 4px 8px;")
        self.text_toolbar.addWidget(self.revert_all_button)
        
        self.text_toolbar.addSeparator()

        self.find_replace_button = QPushButton("Find / Replace")
        self.find_replace_button.setToolTip("Find and replace text across the dataset (Ctrl+F).")
        self.find_replace_button.setStyleSheet("padding: 4px 8px;")
        self.text_toolbar.addWidget(self.find_replace_button)

        self.prefix_suffix_button = QPushButton("Add Prefix/Suffix")
        self.prefix_suffix_button.setToolTip("Add text to the beginning or end of the text files for multiple items.")
        self.prefix_suffix_button.setStyleSheet("padding: 4px 8px;")
        self.text_toolbar.addWidget(self.prefix_suffix_button)

        self.clear_whitespace_button = QPushButton("Clear Lead/Trail Space")
        self.clear_whitespace_button.setToolTip("Remove all leading and trailing whitespace from the text files.")
        self.clear_whitespace_button.setStyleSheet("padding: 4px 8px;")
        self.text_toolbar.addWidget(self.clear_whitespace_button)
        
        self.text_panel_layout.addWidget(self.text_toolbar)

        self.text_editor_panel = TextEditorPanel(MainWindow)
        self.text_panel_layout.addWidget(self.text_editor_panel)
        # --- End Text Editor Panel with Toolbar ---


        self.file_list.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.media_viewer_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.text_panel_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self.main_splitter.addWidget(self.file_list)
        self.main_splitter.addWidget(self.media_viewer_container)
        self.main_splitter.addWidget(self.text_panel_container)
