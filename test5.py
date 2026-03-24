# test5.py
import sys
from PyQt6.QtCore import QCoreApplication, QTimer
from common.config import init_config
from core.logger_manager import LoggerManager
from core.download_service import download_service
from loguru import logger

def test_step5():
    app = QCoreApplication(sys.argv)
    init_config()
    LoggerManager.setup()
    
    # 1. 清理临时文件测试
    download_service.clean_temp()

    # 2. 模拟下载任务
    # 使用之前爬虫测试拿到的真实地址 (復仇母女丼 第一话第一张图)
    test_url = "https://p6.jmpic.xyz/upload_s/2023080101/20230801015646891.webp"
    
    def on_finished(m_id, c_id, i_order, success, path):
        if success:
            logger.success(f"测试下载成功！保存路径: {path}")
        else:
            logger.error("测试下载失败，请检查网络或 Referer")
        # 退出测试
        QTimer.singleShot(500, app.quit)

    # 模拟一个下载请求
    download_service.download_image("1313", 1, 1, test_url)
    
    # 找到刚才的任务并连接信号 (实际开发中由 ImageService 统一处理)
    # 这里为了测试直接手动接一下逻辑
    download_service.signals.finished.connect(on_finished)

    logger.info("下载任务已提交，等待响应...")
    sys.exit(app.exec())

if __name__ == "__main__":
    test_step5()