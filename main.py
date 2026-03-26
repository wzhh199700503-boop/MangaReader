import sys
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer
from loguru import logger 

from common.config import init_config, cfg 
from core.logger_manager import LoggerManager
from core.database import db_manager
from core.update_service import UpdateService
from ui.splash_screen import MangaReaderSplash 
from ui.home_interface import MainWindow 
from qfluentwidgets import setTheme, Theme, setThemeColor

def main():
    init_config()
    LoggerManager.setup()
    
    app = QApplication(sys.argv)
    setThemeColor(cfg.get(cfg.themeColor))
    app.setQuitOnLastWindowClosed(False) 
    
    logo_path = os.path.join("data", "logo.png") 
    splash = MangaReaderSplash(logo_path)
    
    db_manager.init_db()
    
    updater = UpdateService()
    main_window = MainWindow() 

    def on_update_finished(success):
        if success:
            # 补全 6 个参数以匹配新的 update_progress 签名
            splash.update_progress(100, "同步完成，正在准备主界面...", 0, 0, 0, 0)
        else:
            splash.update_progress(95, "同步过程有波动，正在进入...", 0, 0, 0, 0)
        
        QTimer.singleShot(800, lambda: splash.finish_loading(main_window))
        QTimer.singleShot(1000, lambda: [
            main_window.show(),
            app.setQuitOnLastWindowClosed(True) 
        ])

    updater.progressUpdated.connect(splash.update_progress)
    updater.finished.connect(on_update_finished)

    logger.info("启动后台更新线程...")
    updater.start()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()