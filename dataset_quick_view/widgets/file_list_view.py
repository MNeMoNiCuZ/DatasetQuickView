from PyQt6.QtWidgets import QWidget, QListWidget, QListWidgetItem, QVBoxLayout, QSlider, QLabel, QHBoxLayout
from PyQt6.QtCore import Qt, pyqtSignal, QSize, QObject, QThread
from PyQt6.QtGui import QFont, QColor, QPixmap, QIcon
import os

class ThumbnailWorker(QObject):
    thumbnail_ready = pyqtSignal(int, QIcon)

    def process_thumbnails(self, tasks):
        for row, file_path, thumb_size in tasks:
            pixmap = QPixmap(file_path)
            if not pixmap.isNull():
                icon = QIcon(pixmap.scaled(thumb_size, thumb_size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
                self.thumbnail_ready.emit(row, icon)

class FileListView(QWidget):
    currentItemChanged = pyqtSignal(QListWidgetItem, QListWidgetItem)

    def __init__(self, config, dataset):
        super().__init__()
        self.config = config
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
                background-color: transparent;
                border: 2px solid white;
                color: #000000;
            }
            QListWidget::item:selected:!active {
                background-color: transparent;
                border: 2px solid white;
            }
        """)
        layout.addWidget(self.list_widget)

        # Connect signals
        self.list_widget.currentItemChanged.connect(self.currentItemChanged)
        self.list_widget.currentRowChanged.connect(self.sync_slider_to_list)
        self.slider.valueChanged.connect(self.list_widget.setCurrentRow)

        # Thumbnail worker setup
        self.thumbnail_thread = QThread()
        self.thumbnail_worker = ThumbnailWorker()
        self.thumbnail_worker.moveToThread(self.thumbnail_thread)
        self.thumbnail_worker.thumbnail_ready.connect(self.update_thumbnail)
        self.thumbnail_thread.started.connect(lambda: self.thumbnail_worker.process_thumbnails(self._thumbnail_tasks))
        self.thumbnail_thread.start()

        self.apply_view_settings()

    def apply_view_settings(self):
        view_mode = self.config.get_setting('FileList', 'view_mode', 'List')
        thumb_size = int(self.config.get_setting('FileList', 'thumbnail_size', 80))
        grid_layout = self.config.get_bool_setting('FileList', 'grid_layout', False)

        self.list_widget.clear()

        if view_mode == 'Thumbnails':
            self.list_widget.setViewMode(QListWidget.ViewMode.IconMode)
            self.list_widget.setIconSize(QSize(thumb_size, thumb_size))
            self.list_widget.setSpacing(5) # Add spacing between items
            if grid_layout:
                self.list_widget.setResizeMode(QListWidget.ResizeMode.Adjust)
                self.list_widget.setMovement(QListWidget.Movement.Static)
                self.list_widget.setFlow(QListWidget.Flow.LeftToRight)
                self.list_widget.setWrapping(True)
            else:
                self.list_widget.setResizeMode(QListWidget.ResizeMode.Fixed)
                self.list_widget.setMovement(QListWidget.Movement.Static)
                self.list_widget.setFlow(QListWidget.Flow.TopToBottom)
                self.list_widget.setWrapping(False)
        else: # List Mode
            self.list_widget.setViewMode(QListWidget.ViewMode.ListMode)
            self.list_widget.setIconSize(QSize(0, 0))

        self.populate_list(self.dataset.keys())

    def populate_list(self, media_files):
        self.list_widget.clear()
        view_mode = self.config.get_setting('FileList', 'view_mode', 'List')
        thumb_size = int(self.config.get_setting('FileList', 'thumbnail_size', 80))
        grid_layout = self.config.get_bool_setting('FileList', 'grid_layout', False)
        self._thumbnail_tasks = []

        for row, file_path in enumerate(sorted(media_files)):
            item = QListWidgetItem()
            item.setData(Qt.ItemDataRole.UserRole, file_path)
            item.setText(self.get_display_name(file_path))

            if view_mode == 'Thumbnails':
                # In thumbnail mode, hide the text and prepare for an icon
                item.setText('')
                # Add placeholder icon or leave empty for now
                # Add task for background processing
                self._thumbnail_tasks.append((row, file_path, thumb_size))
                # Set a fixed size hint for the item to ensure proper spacing
                item.setSizeHint(QSize(thumb_size + 20, thumb_size + 20)) # Add some padding

            self.list_widget.addItem(item)
        self.update_progress(self.list_widget.currentRow(), self.count())

        # Start processing thumbnails in background if in thumbnail mode
        if view_mode == 'Thumbnails' and self._thumbnail_tasks:
            # Stop and restart thread to process new tasks
            if self.thumbnail_thread.isRunning():
                self.thumbnail_thread.quit()
                self.thumbnail_thread.wait()
            self.thumbnail_thread.start()
        self.list_widget.update() # Force a repaint

    def update_thumbnail(self, row, icon):
        item = self.list_widget.item(row)
        if item:
            item.setIcon(icon)

    def get_media_path_from_text_path(self, text_path):
        for media_path, text_paths in self.dataset.items():
            if text_path in text_paths:
                return media_path
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
                    item.setForeground(QColor("#FAD7A0"))
                else:
                    font.setItalic(False)
                    item.setText(display_name)
                    item.setForeground(QColor("white"))
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
