from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtWidgets import QWidget, QHBoxLayout
from qfluentwidgets import TransparentToolButton, FluentIcon as FIF, BodyLabel

class Pager(QWidget):
    """ 自定义分页器，支持按钮点击和外部键盘事件触发 """
    pageChanged = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_page = 1
        self.total_page = 1
        
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 10, 0, 10)
        
        self.prev_btn = TransparentToolButton(FIF.LEFT_ARROW, self)
        self.next_btn = TransparentToolButton(FIF.RIGHT_ARROW, self)
        self.page_label = BodyLabel("第 1 / 1 页", self)
        
        self.layout.addStretch(1)
        self.layout.addWidget(self.prev_btn)
        self.layout.addWidget(self.page_label)
        self.layout.addWidget(self.next_btn)
        self.layout.addStretch(1)

        self.prev_btn.clicked.connect(self._on_prev_clicked)
        self.next_btn.clicked.connect(self._on_next_clicked)

    def set_total_pages(self, total):
        self.total_page = max(1, total)
        self._update_ui()

    def set_current_page(self, page):
        self.current_page = page
        self._update_ui()

    def _update_ui(self):
        self.page_label.setText(f"第 {self.current_page} / {self.total_page} 页")
        self.prev_btn.setEnabled(self.current_page > 1)
        self.next_btn.setEnabled(self.current_page < self.total_page)

    def _on_prev_clicked(self):
        if self.current_page > 1:
            self.current_page -= 1
            self._update_ui()
            self.pageChanged.emit(self.current_page)

    def _on_next_clicked(self):
        if self.current_page < self.total_page:
            self.current_page += 1
            self._update_ui()
            self.pageChanged.emit(self.current_page)