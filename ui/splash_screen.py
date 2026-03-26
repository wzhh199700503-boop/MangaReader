import os
from PyQt6.QtCore import Qt, QTimer, QSize, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QPixmap, QColor
from PyQt6.QtWidgets import QSplashScreen, QVBoxLayout, QWidget, QGraphicsOpacityEffect
# 引入 CaptionLabel 用于展示辅助统计文字
from qfluentwidgets import ProgressBar, SubtitleLabel, BodyLabel, CaptionLabel, setFont

class MangaReaderSplash(QSplashScreen):
    """A.1 启动页实现"""

    def __init__(self, logo_path, parent=None):
        # 1. 创建基础画布 (稍微加高以容纳统计文字)
        pixmap = QPixmap(QSize(600, 480))
        pixmap.fill(QColor("#fcfcfc")) 
        super().__init__(pixmap, Qt.WindowType.FramelessWindowHint | Qt.WindowType.Window)

        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # 2. 主容器布局
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(40, 40, 40, 40)
        self.layout.setSpacing(15)

        # --- 1.1 Logo 区域 ---
        self.logo_widget = QWidget(self)
        self.logo_layout = QVBoxLayout(self.logo_widget)
        self.logo_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.logo_label = BodyLabel(self.logo_widget)
        if os.path.exists(logo_path):
            self.logo_label.setPixmap(QPixmap(logo_path).scaled(160, 160, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        else:
            self.logo_label.setText("MangaReader")
            setFont(self.logo_label, 24)

        self.opacity_effect = QGraphicsOpacityEffect(self.logo_label)
        self.logo_label.setGraphicsEffect(self.opacity_effect)
        self.logo_layout.addWidget(self.logo_label)

        self.title_label = SubtitleLabel("漫画阅读器", self.logo_widget)
        setFont(self.title_label, 22, 600)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.logo_layout.addWidget(self.title_label)
        self.layout.addWidget(self.logo_widget, stretch=1)

        # --- 1.2 & 1.3 进度与详细统计区域 ---
        self.bottom_widget = QWidget(self)
        self.bottom_layout = QVBoxLayout(self.bottom_widget)
        self.bottom_layout.setSpacing(10)

        # 1.3 状态标签 (显示标题、章节名)
        self.status_label = BodyLabel("正在初始化核心组件...", self.bottom_widget)
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setTextColor(QColor("#666666"), QColor("#aaaaaa"))
        self.bottom_layout.addWidget(self.status_label)

        # 新增：好看的进度统计标签 (漫画: X/Y | 页码: A/B)
        self.stats_label = CaptionLabel("", self.bottom_widget)
        self.stats_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.stats_label.setTextColor(QColor("#999999"), QColor("#888888"))
        self.bottom_layout.addWidget(self.stats_label)

        # 1.2 主进度条
        self.progress_bar = ProgressBar(self.bottom_widget)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setFixedHeight(6)
        self.bottom_layout.addWidget(self.progress_bar)

        self.layout.addWidget(self.bottom_widget)

        # 3. 呼吸灯动画
        self.breath_ani = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.breath_ani.setDuration(2500)
        self.breath_ani.setStartValue(0.5)
        self.breath_ani.setEndValue(1.0)
        self.breath_ani.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self.breath_ani.setLoopCount(-1)
        self.breath_ani.start()

        self.show()

    def update_progress(self, percent, status, curr_m=0, total_m=0, curr_p=0, total_p=0):
        """ 接收 6 参数信号并更新 UI """
        QTimer.singleShot(0, lambda: self._do_update(percent, status, curr_m, total_m, curr_p, total_p))

    def _do_update(self, percent, status, curr_m, total_m, curr_p, total_p):
        self.progress_bar.setValue(percent)
        
        # 截断过长的状态
        display_status = status if len(status) < 45 else status[:42] + "..."
        self.status_label.setText(display_status)
        
        # 更新详细计数文字
        if total_m > 0:
            stats_text = f"漫画：{curr_m} / {total_m}  |  页码：{curr_p} / {total_p}"
            self.stats_label.setText(stats_text)
        
        self.progress_bar.repaint()
        self.status_label.repaint()
        self.stats_label.repaint()

    def finish_loading(self, target_window):
        self.breath_ani.stop()
        self.finish(target_window)

    def mousePressEvent(self, event):
        pass

    def mouseDoubleClickEvent(self, event):
        pass