import os
from PyQt6.QtCore import QThread, pyqtSignal
from loguru import logger
from common.config import cfg
from core.spider_service import spider_service
from core.database import db_manager
from core.request_client import request_client

class UpdateService(QThread):
    """ B.8 更新服务 """
    # 升级信号：(百分比, 状态, 当前漫画, 总漫画, 当前页, 总页数)
    progressUpdated = pyqtSignal(int, str, int, int, int, int)
    finished = pyqtSignal(bool)

    def run(self):
        try:
            # 8.1 获取总数
            self.progressUpdated.emit(0, "正在获取服务器统计...", 0, 0, 0, 0)
            stats = spider_service.fetch_stats() #
            total_pages = stats['total_pages']
            total_mangas = stats['total_manga']
            
            logger.info(f"开始更新流程 | 总页数: {total_pages} | 总漫画数: {total_mangas}")
            processed_count = 0

            # 8.2 遍历每一页
            for page in range(1, total_pages + 1):
                manga_list = spider_service.fetch_manga_list(page) #
                
                # 8.3 遍历该页每一部漫画
                for manga in manga_list:
                    m_id = manga['manga_id']
                    processed_count += 1
                    percent = int((processed_count / total_mangas) * 100)
                    
                    # 8.4 判断是否存在
                    exists = db_manager.manga_exists(m_id)
                    
                    if cfg.get(cfg.isFullUpdated) and exists: #
                        logger.info(f"增量更新完成 | 命中已有漫画: {manga['title']}")
                        self.progressUpdated.emit(100, "数据已是最新", processed_count, total_mangas, page, total_pages)
                        self.finished.emit(True)
                        return

                    if not exists:
                        status = f"同步详情: {manga['title']}"
                        self.progressUpdated.emit(percent, status, processed_count, total_mangas, page, total_pages)
                        
                        # 下载封面
                        cover_ext = manga['cover_url'].split('.')[-1] if '.' in manga['cover_url'] else 'jpg'
                        cover_local = os.path.join(cfg.get(cfg.dataDir), 'manga', m_id, f"cover.{cover_ext}")
                        self._download_cover_sync(manga['cover_url'], cover_local)
                        manga['cover_local_path'] = cover_local

                        # 爬取详情与标签
                        detail = spider_service.fetch_detail(manga['detail_path'])
                        manga.update({
                            "author": detail['author'],
                            "description": detail['description'],
                            "rating": detail['rating']
                        })

                        # 爬取章节图片链接
                        for chap in detail['chapters']:
                            chap_status = f"解析章节: {manga['title']} - {chap['title']}"
                            self.progressUpdated.emit(percent, chap_status, processed_count, total_mangas, page, total_pages)
                            chap['images'] = spider_service.fetch_reading_images(chap['read_path'])

                        # 7.4 事务入库
                        db_manager.insert_manga_full_transaction(
                            manga_info=manga, 
                            chapters=detail['chapters'], 
                            tags=detail.get('tags', [])
                        )

            # 8.5 标记全量完成
            cfg.set(cfg.isFullUpdated, True)
            cfg.save()
            self.progressUpdated.emit(100, "全量同步完成", total_mangas, total_mangas, total_pages, total_pages)
            self.finished.emit(True)

        except Exception as e:
            logger.exception(f"更新服务崩溃: {e}")
            self.finished.emit(False)

    def _download_cover_sync(self, url, path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        resp = request_client.get(url) #
        if resp and resp.status_code == 200:
            with open(path, 'wb') as f:
                f.write(resp.content)