# test3.py
from common.config import init_config
from core.logger_manager import LoggerManager
from core.request_client import request_client
from loguru import logger

def test_step3():
    logger.info("=== 开始测试 Step 3: 请求封装 ===")
    
    # 1. 基础设施点火
    init_config()
    LoggerManager.setup()
    
    # 2. 测试正常请求 (以百度为例)
    test_url = "https://www.baidu.com"
    logger.info(f"正在尝试请求: {test_url}")
    
    resp = request_client.get(test_url)
    if resp and resp.status_code == 200:
        logger.success(f"基础请求测试成功！响应长度: {len(resp.text)}")
    else:
        logger.error("基础请求测试失败")

    # 3. 测试 404 处理 (这是你蓝图中 -1 状态的前置条件)
    not_found_url = "https://www.baidu.com/this_is_a_404_page"
    logger.info(f"正在测试 404 处理: {not_found_url}")
    resp_404 = request_client.get(not_found_url)
    if resp_404 and resp_404.status_code == 404:
        logger.success("404 识别测试成功")

if __name__ == "__main__":
    test_step3()