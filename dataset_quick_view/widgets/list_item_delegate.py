from PyQt6.QtWidgets import QStyledItemDelegate, QStyleOptionViewItem, QStyle
from PyQt6.QtCore import Qt, QRect, QSize
from PyQt6.QtGui import QColor, QPen, QBrush, QPalette

class ListItemDelegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.found_files = set()

    def set_found_files(self, found_files):
        self.found_files = found_files

    def paint(self, painter, option, index):
        # Get the item and its data
        item = self.parent().item(index.row())
        if not item:
            return

        file_path = item.data(Qt.ItemDataRole.UserRole)
        is_found = file_path in self.found_files

        # Get the icon
        icon = item.icon()
        if not icon.isNull():
            # Get the rect for the icon
            rect = option.rect
            icon_size = self.parent().iconSize()
            pixmap = icon.pixmap(icon_size)
            
            # Center the pixmap in the rect
            pixmap_rect = QRect(0, 0, pixmap.width(), pixmap.height())
            pixmap_rect.moveCenter(rect.center())

            # Draw the pixmap
            painter.drawPixmap(pixmap_rect.topLeft(), pixmap)

            # Draw selection indicator
            if option.state & QStyle.StateFlag.State_Selected:
                painter.save()
                pen = QPen(QColor("white"))
                pen.setWidth(2)
                painter.setPen(pen)
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.drawRect(pixmap_rect)
                painter.restore()

            # Draw found indicator
            if is_found:
                painter.save()
                pen = QPen(QColor("yellow"))
                pen.setWidth(2)
                painter.setPen(pen)
                painter.setBrush(Qt.BrushStyle.NoBrush)
                # draw on top of the selection
                painter.drawRect(pixmap_rect.adjusted(-2, -2, 2, 2))
                painter.restore()

    def sizeHint(self, option, index):
        size = super().sizeHint(option, index)
        icon_size = self.parent().iconSize()
        if self.parent().viewMode() == self.parent().viewMode().IconMode:
            return QSize(icon_size.width() + 10, icon_size.height() + 10)
        return size
