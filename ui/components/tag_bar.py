from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtWidgets import QWidget, QHBoxLayout
from qfluentwidgets import SmoothScrollArea, ToggleButton, PushButton

class TagBar(SmoothScrollArea):
    """ 横向滚动的标签选择栏 """
    tagsChanged = pyqtSignal(list) # 当选中标签变化时，发送当前选中的所有标签名称

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(55)
        self.setWidgetResizable(True)
        # 隐藏垂直滚动条，水平滚动条按需显示
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        self.content = QWidget()
        self.layout = QHBoxLayout(self.content)
        self.layout.setContentsMargins(5, 5, 5, 5)
        self.layout.setSpacing(10)
        self.setWidget(self.content)
        
        self.selected_tags = set()
        self.tag_buttons = []

    def load_tags(self, tags):
        """ 初始化加载所有标签 """
        # 清空旧标签
        while self.layout.count():
            item = self.layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        self.selected_tags.clear()
        self.tag_buttons.clear()

        # 增加一个“清除所有”的快捷按钮
        self.clear_btn = PushButton("清除筛选", self.content)
        self.clear_btn.clicked.connect(self.clear_selection)
        self.layout.addWidget(self.clear_btn)

        for tag in tags:
            btn = ToggleButton(tag, self.content)
            # 点击 ToggleButton 时触发
            btn.clicked.connect(lambda checked, t=tag, b=btn: self._on_tag_toggled(checked, t, b))
            self.layout.addWidget(btn)
            self.tag_buttons.append(btn)
            
        self.layout.addStretch(1)

    def _on_tag_toggled(self, checked, tag, btn):
        if checked:
            self.selected_tags.add(tag)
        else:
            self.selected_tags.discard(tag)
        # 发送当前所有选中的标签列表
        self.tagsChanged.emit(list(self.selected_tags))

    def clear_selection(self):
        for btn in self.tag_buttons:
            btn.setChecked(False)
        self.selected_tags.clear()
        self.tagsChanged.emit([])