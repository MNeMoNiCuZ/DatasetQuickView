import os
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QSizePolicy
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtMultimediaWidgets import QVideoWidget
from PyQt6.QtCore import QUrl, Qt
from PyQt6.QtGui import QPixmap

class MediaViewer(QWidget):
    def __init__(self, config=None):
        super().__init__()
        self.config = config
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

        # Image viewer
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Ignored)
        self.layout.addWidget(self.image_label)

        # Video player
        self.video_widget = QVideoWidget()
        self.layout.addWidget(self.video_widget)
        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.player.setAudioOutput(self.audio_output)
        self.player.setVideoOutput(self.video_widget)

        # Start with both hidden
        self.image_label.hide()
        self.video_widget.hide()

    def set_media(self, file_path):
        self.clear_media()
        if not file_path or not os.path.exists(file_path):
            return
            
        ext = os.path.splitext(file_path)[1].lower()
        
        # Get supported formats from config or use defaults
        if self.config:
            supported_formats_str = self.config.get_setting('MediaFormats', 'supported', fallback='.png,.jpg,.jpeg,.bmp,.webp,.gif,.mp4')
        else:
            supported_formats_str = '.png,.jpg,.jpeg,.bmp,.webp,.gif,.mp4'
        
        supported_formats = [f.strip() for f in supported_formats_str.split(',')]
        supported_image_formats = [f for f in supported_formats if f != '.mp4']
        supported_video_formats = ['.mp4']

        if ext in supported_image_formats:
            self.video_widget.hide()
            self.image_label.show()
            pixmap = QPixmap(file_path)
            self.image_label.setPixmap(pixmap.scaled(self.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))

        elif ext in supported_video_formats:
            self.image_label.hide()
            self.video_widget.show()
            self.player.setSource(QUrl.fromLocalFile(file_path))
            
            # Loop video if setting is enabled
            loop = True
            if self.config:
                loop = self.config.get_bool_setting('Video', 'loop', fallback=True)

            if loop:
                self.player.setLoops(-1) # -1 means infinite loop
            else:
                self.player.setLoops(1) # Play once
            self.player.play()

    def clear_media(self):
        self.player.stop()
        self.image_label.hide()
        self.image_label.clear()
        self.video_widget.hide()

    def resizeEvent(self, event):
        # When the widget is resized, scale the pixmap again.
        if self.image_label.pixmap() and not self.image_label.pixmap().isNull():
            current_pixmap = self.image_label.pixmap()
            self.image_label.setPixmap(current_pixmap.scaled(self.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        super().resizeEvent(event)
