# test6.py
import sys
from PyQt6.QtCore import QCoreApplication
from common.config import init_config
from core.logger_manager import LoggerManager
from core.database import db_manager
from core.update_service import UpdateService
from loguru import logger

def test_step6():
    app = QCoreApplication(sys.argv)
    init_config()
    LoggerManager.setup()
    db_manager.init_db()

    worker = UpdateService()
    
    def on_progress(percent, msg):
        print(f"\r进度: [{percent}%] {msg}", end="")

    def on_finished(success):
        print("\n")
        if success:
            logger.success("更新服务测试运行成功！")
        else:
            logger.error("更新服务运行失败。")
        app.quit()

    worker.progressUpdated.connect(on_progress)
    worker.finished.connect(on_finished)
    
    logger.info("启动更新服务测试 (仅同步前几部漫画用于验证)...")
    worker.start()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    test_step6()