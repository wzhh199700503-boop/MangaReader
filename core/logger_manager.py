import sys
import os
from loguru import logger
from common.config import cfg

class LoggerManager:
    """ B.2 日志服务 """
    
    @staticmethod
    def setup():
        # 1. 确定日志路径
        log_path = os.path.join(cfg.get(cfg.dataDir), cfg.get(cfg.logDir))
        os.makedirs(log_path, exist_ok=True)

        # 2. 移除 loguru 默认的 handler
        logger.remove()

        # 3. 配置控制台输出 (2.3: debug 模式下输出所有级别)
        # 如果是 debug 模式，强制 level 为 DEBUG，否则使用配置的 logLevel
        console_level = "DEBUG" if cfg.get(cfg.isDownloadDebug) else cfg.get(cfg.logLevel)
        
        logger.add(
            sys.stdout, 
            level=console_level,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{message}</cyan>",
            enqueue=True
        )

        # 4. 配置物理文件输出 (2.1: 按天分割)
        # 2.2: 自动处理 info, warn, error 分类进入文件
        logger.add(
            os.path.join(log_path, "manga_{time:YYYY-MM-DD}.log"),
            rotation="00:00",      # 每天凌晨分割
            retention="10 days",   # 保留10天
            level="INFO",          # 文件至少记录 INFO 及以上
            encoding="utf-8",
            enqueue=True,          # 异步队列，防止阻塞 IO
            compression="zip"      # 旧日志自动压缩
        )