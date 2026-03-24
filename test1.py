# test1.py
from common.config import init_config, cfg
from core.logger_manager import LoggerManager
from loguru import logger
import os

def test_step1():
    print("=== 开始测试 Step 1: 配置与日志 ===")
    
    # 1. 初始化配置
    init_config()
    
    # 2. 初始化日志
    LoggerManager.setup()
    
    # 3. 验证配置读取
    data_dir = cfg.get(cfg.dataDir)
    logger.info(f"读取配置成功，数据目录为: {data_dir}")
    
    # 4. 测试配置修改与持久化
    original_debug = cfg.get(cfg.isDownloadDebug)
    cfg.set(cfg.isDownloadDebug, True)
    cfg.save()
    logger.success("配置修改并保存成功")
    
    # 5. 测试各级别日志输出
    logger.debug("这条是 DEBUG 日志 (只有 isDownloadDebug 为 True 才会显示)")
    logger.info("这条是 INFO 日志")
    logger.warning("这条是 WARNING 日志")
    logger.error("这条是 ERROR 日志")
    
    # 6. 验证物理日志文件生成
    log_path = os.path.join(data_dir, cfg.get(cfg.logDir))
    logger.info(f"请检查日志目录是否存在: {os.path.abspath(log_path)}")

if __name__ == "__main__":
    test_step1()