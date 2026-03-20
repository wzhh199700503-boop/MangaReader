import asyncio
from core.config_manager import ConfigManager
from core.logger_manager import logger

class SyncManager:
    def __init__(self, db, spider):
        self.db = db
        self.spider = spider
        self.config = ConfigManager()

    async def run_sync(self, progress_callback):
        """
        主同步逻辑
        progress_callback: UI 层的更新函数 (current, total, title)
        """
        # 1. 检查配置确定模式
        is_full_mode = not self.config.get("is_full_synced", False)
        mode_str = "【全量模式】" if is_full_mode else "【增量模式】"
        logger.info(f"开始同步任务 - {mode_str}")

        # 2. 数据库地基检查
        await self.db.init_db()

        # 3. 抓取第一页获取总页数
        try:
            first_page_res = await self.spider.fetch_list_page(1)
            total_pages = first_page_res.get("total_pages", 1)
            logger.info(f"目标站点总页数: {total_pages}")
        except Exception as e:
            logger.error(f"获取首页失败，同步终止: {e}")
            return

        # 进度条估算总数 (1856 是你提供的 HTML 中的总部数)
        # 增量模式下总数设小一点，或者动态根据第一页新番数量展示
        display_total = 1856 if is_full_mode else 30 
        current_sync_count = 0
        should_stop = False

        # 4. 遍历每一页
        for p in range(1, total_pages + 1):
            if should_stop:
                break

            logger.debug(f"正在处理第 {p} 页列表...")
            
            # 第一页已在上面获取，避免重复请求
            if p == 1:
                page_data = first_page_res
            else:
                try:
                    page_data = await self.spider.fetch_list_page(p)
                except Exception as e:
                    logger.error(f"跳过第 {p} 页，请求异常: {e}")
                    continue

            mangas = page_data.get("mangas", [])
            
            # 5. 遍历每一页中的漫画
            for m in mangas:
                m_id = m["manga_id"]
                title = m["title"]

                # 检查本地是否存在
                exists = await self.db.check_manga_exists(m_id)

                if exists:
                    if not is_full_mode:
                        # 【增量模式核心】发现已存在，说明后续无需再爬，直接收工
                        logger.info(f"增量同步命中已存在 ID: {m_id} ({title})，任务提前结束。")
                        should_stop = True
                        break
                    else:
                        # 全量模式下，如果已存在则跳过，去爬下一个不存在的
                        logger.debug(f"全量模式：跳过已存在漫画 {title}")
                        continue

                # 6. 执行“获取一个存一个”
                current_sync_count += 1
                logger.info(f"同步中({current_sync_count}): {title}")
                
                # 通知 UI 更新
                progress_callback(current_sync_count, display_total, title)

                try:
                    # 抓取深度详情
                    detail = await self.spider.fetch_detail(m["manga_url_path"])
                    # 立即写入数据库 (原子操作)
                    await self.db.save_full_manga_data(m, detail)
                    logger.debug(f"数据入库成功: {title}")
                except Exception as e:
                    logger.error(f"同步漫画详情失败 {title}: {e}")

        # 7. 任务收尾
        if is_full_mode and not should_stop:
            self.config.set("is_full_synced", True)
            logger.info("首次全量同步已完成，已更新配置文件。")
        
        logger.info(f"同步流程结束，本次新增/更新: {current_sync_count} 部漫画。")