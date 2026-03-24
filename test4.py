# test4.py
from common.config import init_config
from core.logger_manager import LoggerManager
from core.spider_service import spider_service
from loguru import logger

def test_step4():
    init_config()
    LoggerManager.setup()
    
    logger.info("=== 1. 测试 6.4 数据统计 ===")
    stats = spider_service.fetch_stats()
    logger.success(f"总页数: {stats['total_pages']}, 总漫画数: {stats['total_manga']}")

    logger.info("=== 2. 测试 6.1 列表爬取 (第1页) ===")
    mangas = spider_service.fetch_manga_list(1)
    if mangas:
        first = mangas[0]
        logger.success(f"首部漫画: {first['title']} (ID: {first['manga_id']})")
        
        logger.info("=== 3. 测试 6.2 详情爬取 ===")
        detail = spider_service.fetch_detail(first['detail_path'])
        logger.success(f"作者: {detail['author']}, 章节数: {len(detail['chapters'])}")
        
        if detail['chapters']:
            logger.info("=== 4. 测试 6.3 阅读页爬取 ===")
            imgs = spider_service.fetch_reading_images(detail['chapters'][0]['read_path'])
            logger.success(f"第一章图片数: {len(imgs)}")
    else:
        logger.error("未能爬取到漫画列表")

if __name__ == "__main__":
    test_step4()