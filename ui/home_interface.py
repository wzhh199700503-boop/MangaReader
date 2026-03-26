import math
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout
from qfluentwidgets import (MSFluentWindow, FlowLayout, SmoothScrollArea, 
                            SearchLineEdit, TransparentToolButton, FluentIcon as FIF, 
                            BodyLabel, setFont, NavigationItemPosition)

from core.database import db_manager
from ui.components.manga_card import MangaCard
from ui.components.pager import Pager
from ui.components.tag_bar import TagBar

class LibraryInterface(QWidget):
    """ 漫画库/收藏列表 通用展示页 """
    mangaClicked = pyqtSignal(str) # 通知 MainWindow 切换到详情页

    def __init__(self, title_name, is_favorite_mode=False, parent=None):
        super().__init__(parent)
        self.is_favorite_mode = is_favorite_mode
        self.page_limit = 24
        self.current_search = ""
        self.current_tags = []
        self.is_sort_desc = True
        
        self.setObjectName(title_name)
        
        self.v_layout = QVBoxLayout(self)
        self.v_layout.setContentsMargins(30, 25, 30, 10)
        self.v_layout.setSpacing(10)

        # --- 1. 标题与搜索栏区 ---
        header_layout = QHBoxLayout()
        self.title_label = BodyLabel(title_name, self)
        setFont(self.title_label, 28, 600)
        
        self.search_bar = SearchLineEdit(self)
        self.search_bar.setPlaceholderText("搜索漫画标题...")
        self.search_bar.setFixedWidth(300)
        self.search_bar.searchSignal.connect(self._on_search)
        self.search_bar.clearSignal.connect(lambda: self._on_search(""))
        
        # 排序切换按钮
        self.sort_btn = TransparentToolButton(FIF.UP, self)
        self.sort_btn.setToolTip("当前：最新发布，点击切换正序")
        self.sort_btn.clicked.connect(self._on_sort_toggled)

        header_layout.addWidget(self.title_label)
        header_layout.addStretch(1)
        header_layout.addWidget(self.search_bar)
        header_layout.addWidget(self.sort_btn)
        self.v_layout.addLayout(header_layout)

        # --- 2. 标签栏 (只有漫画库显示，收藏页可按需隐藏) ---
        self.tag_bar = TagBar(self)
        self.tag_bar.tagsChanged.connect(self._on_tags_changed)
        self.v_layout.addWidget(self.tag_bar)
        
        if not self.is_favorite_mode:
            all_tags = db_manager.get_all_tags()
            self.tag_bar.load_tags(all_tags)
        else:
            self.tag_bar.hide() # 收藏页默认隐藏标签栏让空间更大，你也可以打开

        # --- 3. 核心：漫画流式展示区 ---
        self.scroll_area = SmoothScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        
        self.gallery_widget = QWidget()
        self.gallery_widget.setStyleSheet("background: transparent;")
        self.flow_layout = FlowLayout(self.gallery_widget)
        self.flow_layout.setAnimation(250)
        self.flow_layout.setContentsMargins(0, 10, 0, 10)
        self.flow_layout.setSpacing(20)
        
        self.scroll_area.setWidget(self.gallery_widget)
        self.v_layout.addWidget(self.scroll_area, stretch=1)

        # --- 4. 分页器 ---
        self.pager = Pager(self)
        self.pager.pageChanged.connect(self._load_data)
        self.v_layout.addWidget(self.pager)

        # 初始化加载第一页数据
        self._load_data(1)

    def keyPressEvent(self, e):
        """ 支持键盘 Left/Right 翻页 """
        if e.key() == Qt.Key.Key_Left:
            self.pager._on_prev_clicked()
        elif e.key() == Qt.Key.Key_Right:
            self.pager._on_next_clicked()
        super().keyPressEvent(e)

    def _on_search(self, text):
        self.current_search = text
        self._load_data(1) # 搜索时重置为第一页

    def _on_tags_changed(self, tags):
        self.current_tags = tags
        self._load_data(1)

    def _on_sort_toggled(self):
        self.is_sort_desc = not self.is_sort_desc
        icon = FIF.UP if self.is_sort_desc else FIF.DOWN
        self.sort_btn.setIcon(icon)
        self.sort_btn.setToolTip("当前：最新发布" if self.is_sort_desc else "当前：最早发布")
        self._load_data(1)

    def _load_data(self, page):
        """ 核心数据加载组装逻辑 """
        # 清空画廊
        while self.flow_layout.count():
            item = self.flow_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # 1. 计算总页数
        total_count = db_manager.get_total_count(self.current_search, self.current_tags, self.is_favorite_mode)
        total_pages = math.ceil(total_count / self.page_limit)
        
        self.pager.set_total_pages(total_pages)
        self.pager.set_current_page(page)

        # 2. 拉取数据并渲染卡片
        manga_list = db_manager.get_manga_list(
            page=page, 
            limit=self.page_limit, 
            search=self.current_search, 
            tags=self.current_tags, 
            sort_desc=self.is_sort_desc,
            is_favorite=self.is_favorite_mode
        )

        for row in manga_list:
            m_id, title, author, cover_path = row
            card = MangaCard(m_id, title, author, cover_path, self.gallery_widget)
            card.clicked.connect(self.mangaClicked.emit)
            self.flow_layout.addWidget(card)


class MainWindow(MSFluentWindow):
    """ A.2 主窗口：集成导航栏 """
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MangaReader")
        self.resize(1150, 850)
        
        # 居中显示
        desktop = self.screen().availableGeometry()
        self.move(int((desktop.width() - self.width()) / 2),
                  int((desktop.height() - self.height()) / 2))

        # 1. 初始化页面 (复用 LibraryInterface，仅参数不同)
        self.library_interface = LibraryInterface("我的漫画库", is_favorite_mode=False, parent=self)
        self.favorite_interface = LibraryInterface("收藏列表", is_favorite_mode=True, parent=self)
        
        # TODO: self.setting_interface = SettingInterface(self)
        self.setting_interface = QWidget() # 占位
        self.setting_interface.setObjectName("SettingInterface")

        # 2. 绑定页面跳转信号 (占位打印，后续接入详情页)
        self.library_interface.mangaClicked.connect(lambda m_id: print(f"主库点击: {m_id}"))
        self.favorite_interface.mangaClicked.connect(lambda m_id: print(f"收藏点击: {m_id}"))

        # 3. 添加到侧边导航栏
        self.addSubInterface(self.library_interface, FIF.HOME, "漫画库")
        self.addSubInterface(self.favorite_interface, FIF.HEART, "收藏列表")
        self.addSubInterface(self.setting_interface, FIF.SETTING, "设置", NavigationItemPosition.BOTTOM)