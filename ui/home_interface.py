import os
from PyQt6.QtCore import Qt, QSize, pyqtSignal
from PyQt6.QtGui import QPixmap, QIcon
from PyQt6.QtWidgets import QWidget, QVBoxLayout
from qfluentwidgets import (FlowLayout, CardWidget, BodyLabel, CaptionLabel,
                            ImageLabel, SmoothScrollArea, MSFluentWindow,
                            FluentIcon as FIF, setFont)

from core.database import db_manager
from common.config import cfg

class MangaCard(CardWidget):
    """ D.9.2 漫画磁贴组件：展示封面、标题与作者 """
    clicked = pyqtSignal(str) # 点击信号，传递 manga_id

    def __init__(self, manga_id, title, author, cover_path, parent=None):
        super().__init__(parent)
        self.manga_id = manga_id
        # 设置卡片固定大小，确保流式布局整齐
        self.setFixedSize(160, 265)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(8, 8, 8, 8)
        self.layout.setSpacing(5)

        # 1. 封面图展示 (ImageLabel 支持圆角)
        self.cover_label = ImageLabel(self)
        self.cover_label.setFixedSize(144, 195)
        self.cover_label.setBorderRadius(4, 4, 4, 4)

        # 校验本地封面路径
        if os.path.exists(cover_path):
            self.cover_label.setImage(cover_path)
        else:
            self.cover_label.setText("暂无封面")

        self.layout.addWidget(self.cover_label, 0, Qt.AlignmentFlag.AlignCenter)

        # 2. 标题 (粗体，鼠标悬停显示完整标题)
        self.title_label = BodyLabel(title, self)
        self.title_label.setToolTip(title)
        setFont(self.title_label, 13, 600)
        self.layout.addWidget(self.title_label)

        # 3. 作者信息
        self.author_label = CaptionLabel(author, self)
        self.author_label.setTextColor("#666666", "#aaaaaa")
        self.layout.addWidget(self.author_label)

    def mouseReleaseEvent(self, e):
        """ 鼠标释放时发射点击信号 """
        super().mouseReleaseEvent(e)
        self.clicked.emit(self.manga_id)


class HomeInterface(SmoothScrollArea):
    """ D.9.2 主页界面：漫画库流式展示页 """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.view = QWidget(self)
        self.root_layout = QVBoxLayout(self.view)
        self.root_layout.setContentsMargins(30, 25, 30, 25)

        # 1. 页面大标题
        self.title_label = BodyLabel("我的漫画库", self.view)
        setFont(self.title_label, 28, 600)
        self.root_layout.addWidget(self.title_label)

        # 2. 核心：FlowLayout 流式布局
        # 当窗口缩放时，卡片会自动换行
        self.flow_layout = FlowLayout()
        self.flow_layout.setAnimation(250) # 启用优雅的排列动画
        self.flow_layout.setSpacing(20)
        self.flow_layout.setContentsMargins(0, 15, 0, 15)
        self.root_layout.addLayout(self.flow_layout)

        # 底部填充，确保卡片靠顶对齐
        self.root_layout.addStretch(1)

        self.setWidget(self.view)
        self.setWidgetResizable(True)
        self.setObjectName("homeInterface")

        # 从数据库加载漫画数据
        self.load_mangas()

    def load_mangas(self):
        """ 从数据库拉取所有漫画并渲染卡片 """
        # 清空现有布局，防止重复加载
        while self.flow_layout.count():
            item = self.flow_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # 获取数据库连接并查询
        conn = db_manager.get_connection()
        cursor = conn.execute("SELECT manga_id, title, author, cover_local_path FROM manga")

        for row in cursor.fetchall():
            m_id, title, author, cover_path = row
            # 创建漫画卡片
            card = MangaCard(m_id, title, author, cover_path, self.view)
            card.clicked.connect(self._on_card_clicked)
            self.flow_layout.addWidget(card)

    def _on_card_clicked(self, manga_id):
        """ 处理漫画点击事件 """
        print(f"DEBUG: 准备打开漫画详情 ID: {manga_id}")
        # TODO: 发送信号至 MainWindow 切换到详情页


class MainWindow(MSFluentWindow):
    """ A.2 主窗口：采用 MSFluentWindow (微软商店风格) """
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MangaReader")

        # 1. 初始化子页面
        self.home_interface = HomeInterface(self)
        # TODO: self.setting_interface = SettingInterface(self)

        # 2. 将子页面添加到侧边导航栏
        self.addSubInterface(self.home_interface, FIF.HOME, "主页")

        # 3. 窗口基础设置
        self.resize(1100, 850)
        
        # 窗口居中逻辑
        desktop = self.screen().availableGeometry()
        self.move(int((desktop.width() - self.width()) / 2),
                  int((desktop.height() - self.height()) / 2))

    def closeEvent(self, event):
        """ 覆盖关闭事件，确保主循环彻底退出 """
        from PyQt6.QtWidgets import QApplication
        super().closeEvent(event)
        # 恢复应用退出逻辑，防止后台线程(UpdateService)成为孤儿进程
        QApplication.instance().setQuitOnLastWindowClosed(True)