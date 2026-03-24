# test7.py
import sys
import os
from PyQt6.QtCore import QCoreApplication, QTimer
from common.config import init_config
from core.logger_manager import LoggerManager
from core.image_service import image_service
from loguru import logger

def test_step7():
    app = QCoreApplication(sys.argv)
    init_config()
    LoggerManager.setup()
    
    # 准备测试数据 (复用之前的复仇母女丼 ID: 1313)
    m_id = "1313"
    c_id = 1
    i_order = 1
    test_url = "https://p6.jmpic.xyz/upload_s/2023080101/20230801015646891.webp"

    # 信号接收器
    def on_image_ready(manga_id, chap_id, order, path):
        logger.success(f"UI 收到信号！图片已就绪: {path}")
        # 验证物理文件
        if os.path.exists(path):
            logger.info("物理文件校验通过")
        
        # 测试完毕，退出循环
        QTimer.singleShot(500, app.quit)

    # 连接 UI 层的信号
    image_service.imageReady.connect(on_image_ready)

    logger.info(f"正在请求图片: {m_id}_{c_id}_{i_order}")
    
    # 模拟 UI 发起请求
    # 第一次运行：应该触发下载
    # 第二次运行：应该直接命中缓存
    image_service.get_image(m_id, c_id, i_order, test_url)

    sys.exit(app.exec())

if __name__ == "__main__":
    test_step7()