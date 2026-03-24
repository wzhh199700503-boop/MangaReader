import os
from PyQt6.QtCore import Qt, QTimer, QSize, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QPixmap, QIcon, QColor
from PyQt6.QtWidgets import QSplashScreen, QVBoxLayout, QWidget, QGraphicsOpacityEffect
from qfluentwidgets import ProgressBar, SubtitleLabel, BodyLabel, setFont, theme

from common.config import cfg

class MangaReaderSplash(QSplashScreen):
    """ A.1 启动页实现 """
    
    def __init__(self, logo_path, parent=None):
        # 1. 创建基础画布 (稍微大一点以容纳下方控件)
        pixmap = QPixmap(QSize(600, 450))
        pixmap.fill(QColor("#fcfcfc")) # QFluentWidgets 默认背景色
        super().__init__(pixmap, Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.FramelessWindowHint)
        
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # 2. 主容器布局
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(30, 30, 30, 30)
        self.layout.setSpacing(15)

        # --- 1.1 Logo 区域 (带呼吸灯) ---
        self.logo_widget = QWidget(self)
        self.logo_layout = QVBoxLayout(self.logo_widget)
        self.logo_layout.setContentsMargins(0, 0, 0, 0)
        self.logo_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Logo 图片标签
        self.logo_label = BodyLabel(self.logo_widget)
        if os.path.exists(logo_path):
            self.logo_label.setPixmap(QPixmap(logo_path).scaled(
                QSize(160, 160), 
                Qt.AspectRatioMode.KeepAspectRatio, 
                Qt.TransformationMode.SmoothTransformation
            ))
        else:
            # 没图时显示文字占位
            self.logo_label.setText("MangaReader Logo")
            setFont(self.logo_label, 24)

        # 应用不透明度特效用于动画
        self.opacity_effect = QGraphicsOpacityEffect(self.logo_label)
        self.logo_label.setGraphicsEffect(self.opacity_effect)
        self.logo_layout.addWidget(self.logo_label)
        
        # 标题
        self.title_label = SubtitleLabel("漫画阅读器", self.logo_widget)
        setFont(self.title_label, 20)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.logo_layout.addWidget(self.title_label)

        # 将 Logo 区域加入主布局
        self.layout.addWidget(self.logo_widget, stretch=1)

        # --- 1.2 & 1.3 进度与状态区域 ---
        self.bottom_widget = QWidget(self)
        self.bottom_layout = QVBoxLayout(self.bottom_widget)
        self.bottom_layout.setContentsMargins(0, 0, 0, 0)
        self.bottom_layout.setSpacing(8)

        # 1.3 展示当前正在做什么的标签
        self.status_label = BodyLabel("正在初始化核心组件...", self.bottom_widget)
        self.status_label.setWordWrap(True)
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setTextColor(QColor("#666666"), QColor("#aaaaaa"))
        self.bottom_layout.addWidget(self.status_label)

        # 1.2 总进度的进度条 ProgressBar
        self.progress_bar = ProgressBar(self.bottom_widget)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFixedHeight(6)
        self.bottom_layout.addWidget(self.progress_bar)

        self.layout.addWidget(self.bottom_widget)

        # 3. 设置呼吸灯动画 (0.6 opacity -> 1.0 opacity)
        self.breath_ani = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.breath_ani.setDuration(2500) # 2.5s 一个周期
        self.breath_ani.setStartValue(0.6)
        self.breath_ani.setEndValue(1.0)
        self.breath_ani.setEasingCurve(QEasingCurve.Type.InOutQuad) # 平滑
        self.breath_ani.setLoopCount(-1) # 无限循环
        self.breath_ani.start()

        self.show()

    def update_progress(self, percent: int, status: str):
        """ 绑定到 UpdateService 信号的槽函数 """
        # 使用线程安全的方式更新 UI
        QTimer.singleShot(0, lambda: self._do_update(percent, status))

    def _do_update(self, percent: int, status: str):
        self.progress_bar.setValue(percent)
        # 截断过长的状态，防止撑破 UI
        display_status = status if len(status) < 40 else status[:37] + "..."
        self.status_label.setText(display_status)
        # 确保立刻重绘
        self.progress_bar.repaint()
        self.status_label.repaint()

    def finish_loading(self, target_window):
        """ 动画完成后切换窗口 """
        self.breath_ani.stop()
        self.finish(target_window)

    def mousePressEvent(self, event):
        # 重写此方法但不写任何内容，即可禁用“点击即关闭”
        pass
    
    # 也可以顺便拦截双击
    def mouseDoubleClickEvent(self, event):
        pass