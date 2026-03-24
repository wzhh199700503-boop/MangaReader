import sys
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer
from loguru import logger # <--- 补上这个导入

from common.config import init_config
from core.logger_manager import LoggerManager
from core.database import db_manager
from core.update_service import UpdateService
from ui.splash_screen import MangaReaderSplash # 确保路径正确
from ui.home_interface import MainWindow # 假设你已经把 MainWindow 移到了界面文件

def main():
    init_config()
    LoggerManager.setup()
    
    # 强制开启应用
    app = QApplication(sys.argv)
    # 确保即使没有窗口，程序也不会在启动阶段直接退出
    app.setQuitOnLastWindowClosed(False) 
    
    logo_path = os.path.join("data", "logo.png") 
    splash = MangaReaderSplash(logo_path)
    
    db_manager.init_db()
    
    updater = UpdateService()
    main_window = MainWindow() # 这里会触发 HomeInterface 的 load_mangas

    def on_update_finished(success):
        if success:
            splash.update_progress(100, "同步完成，正在准备主界面...")
        else:
            splash.update_progress(95, "同步过程有波动，正在进入...")
        
        # 优雅过渡
        QTimer.singleShot(800, lambda: splash.finish(main_window))
        QTimer.singleShot(1000, lambda: [
            main_window.show(),
            app.setQuitOnLastWindowClosed(True) # 此时恢复“最后一个窗口关闭则退出”的逻辑
        ])

    updater.progressUpdated.connect(splash.update_progress)
    updater.finished.connect(on_update_finished)

    updater.start()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()