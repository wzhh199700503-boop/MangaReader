# test2.py
from common.config import init_config
from core.logger_manager import LoggerManager
from core.database import db_manager
from loguru import logger
import os

def test_step2():
    logger.info("=== 开始测试 Step 2: 数据库初始化 ===")
    
    # 1. 必须先初始化基础设施
    init_config()
    LoggerManager.setup()
    
    # 2. 执行数据库初始化
    try:
        db_manager.init_db()
        
        # 3. 验证连接并检查物理文件
        conn = db_manager.get_connection()
        db_file = db_manager.db_path
        
        if os.path.exists(db_file):
            logger.success(f"数据库文件已创建: {os.path.abspath(db_file)}")
            
            # 尝试查一下表结构，验证是否真的建好了
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [row[0] for row in cursor.fetchall()]
            logger.info(f"数据库中的表: {', '.join(tables)}")
            
        else:
            logger.error("数据库文件创建失败！")
            
    except Exception as e:
        logger.exception(f"数据库测试过程发生异常: {e}")

if __name__ == "__main__":
    test_step2()