import logging
import os
import sys
from logging.handlers import TimedRotatingFileHandler
from core.config_manager import ConfigManager

class LogManager:
    def __init__(self, log_dir="logs", debug_mode=False):
        self.log_dir = log_dir
        os.makedirs(self.log_dir, exist_ok=True)
        
        self.logger = logging.getLogger("MangaReader")
        self.logger.setLevel(logging.DEBUG) # 顶层设为 DEBUG，由 Handler 过滤
        self.logger.handlers.clear() # 防止重复添加 Handler

        # 1. 统一的格式：[2026-03-20 18:00:00] [INFO] Message
        formatter = logging.Formatter(
            '[%(asctime)s] [%(levelname)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        # 2. 文件 Handler (按天切割，保留30天)
        file_handler = TimedRotatingFileHandler(
            filename=os.path.join(self.log_dir, "app.log"),
            when="midnight",
            interval=1,
            backupCount=30,
            encoding="utf-8"
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.INFO) # 文件默认只记 INFO 及以上
        self.logger.addHandler(file_handler)

        # 3. 控制台 Handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        
        # 核心逻辑：如果开启 debug_mode，控制台打印 DEBUG 及以上，否则只打印 INFO
        if debug_mode:
            console_handler.setLevel(logging.DEBUG)
        else:
            console_handler.setLevel(logging.INFO)
            
        self.logger.addHandler(console_handler)

    def get_logger(self):
        return self.logger

# --- 逻辑修正：先实例化配置，再传给日志 ---
_config_temp = ConfigManager()
logger = LogManager(debug_mode=_config_temp.get("debug_mode", False)).get_logger()