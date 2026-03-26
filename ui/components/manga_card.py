import os
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QVBoxLayout
from qfluentwidgets import CardWidget, BodyLabel, CaptionLabel, ImageLabel, setFont

class MangaCard(CardWidget):
    clicked = pyqtSignal(str) 

    def __init__(self, manga_id, title, author, cover_path, parent=None):
        super().__init__(parent)
        self.manga_id = manga_id
        self.setFixedSize(160, 265)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(8, 8, 8, 8)
        self.layout.setSpacing(5)

        self.cover_label = ImageLabel(self)
        self.cover_label.setFixedSize(144, 195)
        self.cover_label.setBorderRadius(4, 4, 4, 4)

        if os.path.exists(cover_path):
            self.cover_label.setImage(cover_path)
        else:
            self.cover_label.setText("暂无封面")

        self.layout.addWidget(self.cover_label, 0, Qt.AlignmentFlag.AlignCenter)

        self.title_label = BodyLabel(title, self)
        self.title_label.setToolTip(title)
        setFont(self.title_label, 13, 600)
        self.layout.addWidget(self.title_label)

        self.author_label = CaptionLabel(author, self)
        self.author_label.setTextColor("#666666", "#aaaaaa")
        self.layout.addWidget(self.author_label)

    def mouseReleaseEvent(self, e):
        super().mouseReleaseEvent(e)
        self.clicked.emit(self.manga_id)