
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QTabWidget, QWidget, QFormLayout, QCheckBox, QDialogButtonBox, QSpinBox, QComboBox, QLineEdit
from PyQt6.QtGui import QIntValidator
from ..utils.config_manager import ConfigManager


class SettingsDialog(QDialog):
    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config
        self.setWindowTitle("Settings")
        self.setMinimumWidth(400)

        self.layout = QVBoxLayout(self)
        self.tabs = QTabWidget()
        self.layout.addWidget(self.tabs)

        self.file_list_tab = QWidget()
        self.tabs.addTab(self.file_list_tab, "File List")
        self.setup_file_list_tab()

        self.media_formats_tab = QWidget()
        self.tabs.addTab(self.media_formats_tab, "Media Formats")
        self.setup_media_formats_tab()

        self.video_tab = QWidget()
        self.tabs.addTab(self.video_tab, "Video")
        self.setup_video_tab()

        self.program_tab = QWidget()
        self.tabs.addTab(self.program_tab, "Program")
        self.setup_program_tab()

        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.layout.addWidget(self.button_box)

    def setup_file_list_tab(self):
        layout = QFormLayout()
        self.file_list_tab.setLayout(layout)

        self.view_mode_combo = QComboBox()
        self.view_mode_combo.addItems(["List", "Thumbnails"])
        current_mode = self.config.get_setting('FileList', 'view_mode', 'List')
        self.view_mode_combo.setCurrentText(current_mode)
        layout.addRow("View Mode:", self.view_mode_combo)

        self.thumbnail_size_lineedit = QLineEdit()
        self.thumbnail_size_lineedit.setText(self.config.get_setting('FileList', 'thumbnail_size', '80'))
        self.thumbnail_size_lineedit.setValidator(QIntValidator(1, 9999, self))
        layout.addRow("Thumbnail Size:", self.thumbnail_size_lineedit)

        self.grid_layout_checkbox = QCheckBox("Display thumbnails in a grid")
        self.grid_layout_checkbox.setChecked(self.config.get_bool_setting('FileList', 'grid_layout', False))
        layout.addRow(self.grid_layout_checkbox)

    def setup_media_formats_tab(self):
        layout = QFormLayout()
        self.media_formats_tab.setLayout(layout)

        self.media_format_checkboxes = {}
        supported_formats = self.config.get_setting('MediaFormats', 'supported', fallback='.png,.jpg,.jpeg,.bmp,.webp,.gif,.mp4')
        
        for fmt in supported_formats.split(','):
            fmt = fmt.strip()
            if not fmt:
                continue
            
            checkbox = QCheckBox()
            is_enabled = self.config.get_bool_setting('MediaFormats', fmt.replace('.', ''), fallback=True)
            checkbox.setChecked(is_enabled)
            self.media_format_checkboxes[fmt] = checkbox
            layout.addRow(f"*{fmt}", checkbox)

    def setup_video_tab(self):
        layout = QFormLayout()
        self.video_tab.setLayout(layout)
        self.loop_video_checkbox = QCheckBox("Loop video playback")
        self.loop_video_checkbox.setChecked(self.config.get_bool_setting('Video', 'loop', fallback=True))
        layout.addRow(self.loop_video_checkbox)

    def setup_program_tab(self):
        layout = QFormLayout()
        self.program_tab.setLayout(layout)
        self.file_list_width_spinbox = QSpinBox()
        self.file_list_width_spinbox.setRange(100, 2000)
        self.file_list_width_spinbox.setValue(int(self.config.get_setting('Program', 'file_list_width', fallback=250)))
        layout.addRow("File List Width:", self.file_list_width_spinbox)

        self.text_editor_width_spinbox = QSpinBox()
        self.text_editor_width_spinbox.setRange(100, 2000)
        self.text_editor_width_spinbox.setValue(int(self.config.get_setting('Program', 'text_editor_width', fallback=300)))
        layout.addRow("Text Editor Width:", self.text_editor_width_spinbox)

    def accept(self):
        # File List settings
        self.config.set_setting('FileList', 'view_mode', self.view_mode_combo.currentText())
        self.config.set_setting('FileList', 'thumbnail_size', self.thumbnail_size_lineedit.text())
        self.config.set_setting('FileList', 'grid_layout', str(self.grid_layout_checkbox.isChecked()))

        # Media Formats settings
        for fmt, checkbox in self.media_format_checkboxes.items():
            self.config.set_setting('MediaFormats', fmt.replace('.', ''), str(checkbox.isChecked()))
        
        # Video settings
        loop_is_checked = self.loop_video_checkbox.isChecked()
        self.config.set_setting('Video', 'loop', str(loop_is_checked))

        # Program settings
        self.config.set_setting('Program', 'file_list_width', str(self.file_list_width_spinbox.value()))
        self.config.set_setting('Program', 'text_editor_width', str(self.text_editor_width_spinbox.value()))

        self.config.save_config()
        super().accept()
