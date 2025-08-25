from PyQt6.QtWidgets import QWidget, QListWidget, QListWidgetItem, QVBoxLayout, QSlider, QLabel, QHBoxLayout
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor
import os

class FileListView(QWidget):
    currentItemChanged = pyqtSignal(QListWidgetItem, QListWidgetItem)

    def __init__(self, dataset):
        super().__init__()
        self.dataset = dataset if dataset is not None else {}

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        # Navigation layout
        nav_layout = QHBoxLayout()
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.slider.setStyleSheet("""
            QSlider::groove:horizontal {
                border: 1px solid #888888;
                border-radius: 3px;
                height: 10px;
                margin: 0px;
                background-color: #555555;
            }
            QSlider::handle:horizontal {
                background-color: #b0b0b0;
                border: 1px solid #888888;
                width: 5px;
                margin: -2px 0;
                border-radius: 2px;
            }
            QSlider::sub-page:horizontal {
                background-color: #b0b0b0;
                border: 1px solid #888888;
                border-radius: 3px;
            }
        """)
        self.progress_label = QLabel("0 / 0")
        nav_layout.addWidget(self.slider)
        nav_layout.addWidget(self.progress_label)
        layout.addLayout(nav_layout)

        self.list_widget = QListWidget()
        self.list_widget.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.list_widget.setStyleSheet("""
            QListWidget { border: none; }
            QListWidget::item:selected {
                background-color: #e0e0e0;
                color: #000000;
            }
        """)
        layout.addWidget(self.list_widget)

        # Connect signals
        self.list_widget.currentItemChanged.connect(self.currentItemChanged)
        self.list_widget.currentRowChanged.connect(self.sync_slider_to_list)
        self.slider.valueChanged.connect(self.list_widget.setCurrentRow)

        self.populate_list(self.dataset.keys())

    def populate_list(self, media_files):
        self.list_widget.clear()
        for file_path in sorted(media_files):
            item = QListWidgetItem(self.get_display_name(file_path))
            item.setData(Qt.ItemDataRole.UserRole, file_path)
            self.list_widget.addItem(item)
        self.update_progress(self.list_widget.currentRow(), self.count())

    def get_media_path_from_text_path(self, text_path):
        # First, check if it's an existing file in the dataset
        for media_path, text_paths in self.dataset.items():
            if text_path in text_paths:
                return media_path
        
        # If not found in dataset, it might be a new file.
        # Assume its media_path is the same as its basename with a media extension.
        text_basename_no_ext = os.path.splitext(os.path.basename(text_path))[0]
        text_dir = os.path.dirname(text_path)

        for media_path_in_dataset in self.dataset.keys():
            media_dir = os.path.dirname(media_path_in_dataset)
            media_basename_no_ext = os.path.splitext(os.path.basename(media_path_in_dataset))[0]
            
            if text_dir == media_dir and text_basename_no_ext == media_basename_no_ext:
                return media_path_in_dataset
        
        return None

    def set_item_dirty(self, media_path, is_dirty):
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.data(Qt.ItemDataRole.UserRole) == media_path:
                font = item.font()
                display_name = self.get_display_name(media_path)
                if is_dirty:
                    font.setItalic(True)
                    item.setText(f"{display_name} *")
                    item.setForeground(QColor("#FAD7A0")) # A light orange color
                else:
                    font.setItalic(False)
                    item.setText(display_name)
                    item.setForeground(QColor("white")) # Default text color
                item.setFont(font)
                break

    def sync_slider_to_list(self, row):
        if self.slider.value() != row:
            self.slider.blockSignals(True)
            self.slider.setValue(row)
            self.slider.blockSignals(False)
        self.update_progress(row, self.count())

    def update_progress(self, current, total):
        if total > 0:
            self.slider.setRange(0, total - 1)
            self.slider.setValue(current)
            self.progress_label.setText(f"{current + 1} / {total}")
        else:
            self.slider.setRange(0, 0)
            self.progress_label.setText("0 / 0")

    def get_display_name(self, file_path):
        return os.path.basename(file_path)

    def setFont(self, font):
        self.list_widget.setFont(font)

    def count(self):
        return self.list_widget.count()

    def currentRow(self):
        return self.list_widget.currentRow()

    def setCurrentRow(self, row):
        self.list_widget.setCurrentRow(row)

    def currentItem(self):
        return self.list_widget.currentItem()


