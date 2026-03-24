import os
import shutil
from PyQt6.QtCore import QObject, QRunnable, pyqtSignal, QThreadPool, pyqtSlot
from loguru import logger
from common.config import cfg
from core.request_client import request_client


class DownloadSignals(QObject):
    """5.3 失败/成功反馈信号"""

    # 信号参数: (manga_id, chapter_id, image_order, success, file_path)
    finished = pyqtSignal(str, int, int, bool, str)


class DownloadWorker(QRunnable):
    """单个图片的下载执行单元"""

    def __init__(self, manga_id, chapter_id, image_order, url, save_path, tmp_path):
        super().__init__()
        self.manga_id = manga_id
        self.chapter_id = chapter_id
        self.image_order = image_order
        self.url = url
        self.save_path = save_path
        self.tmp_path = tmp_path
        self.signals = DownloadSignals()

    @pyqtSlot()
    def run(self):
        # 5.4 重试机制已在 request_client 中通过 urllib3 实现
        resp = request_client.get(self.url, stream=True)

        if resp and resp.status_code == 200:
            try:
                # 5.5 写入临时文件
                os.makedirs(os.path.dirname(self.tmp_path), exist_ok=True)
                with open(self.tmp_path, "wb") as f:
                    for chunk in resp.iter_content(chunk_size=8192):
                        f.write(chunk)

                # 原子性重命名：确保文件完整性
                os.makedirs(os.path.dirname(self.save_path), exist_ok=True)
                shutil.move(self.tmp_path, self.save_path)

                self.signals.finished.emit(
                    self.manga_id,
                    self.chapter_id,
                    self.image_order,
                    True,
                    self.save_path,
                )
            except Exception as e:
                logger.error(f"文件IO错误: {e}")
                if os.path.exists(self.tmp_path):
                    os.remove(self.tmp_path)
                self.signals.finished.emit(
                    self.manga_id, self.chapter_id, self.image_order, False, ""
                )
        else:
            # 可能是 404 等无法修复的错误
            self.signals.finished.emit(
                self.manga_id, self.chapter_id, self.image_order, False, ""
            )


class DownloadService(QObject):
    """B.5 章节图片下载服务"""

    def __init__(self):
        super().__init__()
        # --- 修复点：增加一个全局信号中心 ---
        self.signals = DownloadSignals()
        self.thread_pool = QThreadPool()
        # 从配置读取并发数
        self.thread_pool.setMaxThreadCount(cfg.get(cfg.concurrentTasks))
        # 5.1 任务去重字典: { "m_c_p": signals }
        self.active_tasks = {}

    def clean_temp(self):
        """5.5 清理临时文件 (程序启动时调用)"""
        tmp_dir = os.path.join(cfg.get(cfg.dataDir), "temp")
        if os.path.exists(tmp_dir):
            shutil.rmtree(tmp_dir)
            logger.info("已清理所有残余的 .tmp 临时文件")
        os.makedirs(tmp_dir, exist_ok=True)

    def download_image(self, manga_id, chapter_id, image_order, url, ext="webp"):
        """对外提供的下载接口"""
        # 构造物理路径 (C.2.3: 左补零至3位)
        file_name = f"{image_order:03d}.{ext}"
        save_path = os.path.join(
            cfg.get(cfg.dataDir), "manga", str(manga_id), str(chapter_id), file_name
        )

        # 任务唯一标识
        task_key = f"{manga_id}_{chapter_id}_{image_order}"

        # 1. 物理检查：如果正式文件已存在，直接返回成功
        if os.path.exists(save_path):
            return True

        # 2. 5.1 任务去重：如果已经在下载中，不再创建新任务
        if task_key in self.active_tasks:
            logger.debug(f"任务已在队列中，跳过: {task_key}")
            return False

        # 3. 创建临时路径
        tmp_path = os.path.join(cfg.get(cfg.dataDir), "temp", f"{task_key}.tmp")

        # 4. 创建并提交 Worker
        worker = DownloadWorker(
            manga_id, chapter_id, image_order, url, save_path, tmp_path
        )
        worker.signals.finished.connect(self._on_task_finished)

        self.active_tasks[task_key] = worker
        self.thread_pool.start(worker)
        return False

    def _on_task_finished(self, m_id, c_id, i_order, success, path):
        task_key = f"{m_id}_{c_id}_{i_order}"
        if task_key in self.active_tasks:
            del self.active_tasks[task_key]
        self.signals.finished.emit(m_id, c_id, i_order, success, path)
        from core.database import db_manager

        if success:
            db_manager.update_image_status(m_id, c_id, i_order, 1)
            logger.debug(f"下载成功: {task_key}")
        else:
            db_manager.update_image_status(m_id, c_id, i_order, -1)
            logger.warning(f"下载失败: {task_key}")


download_service = DownloadService()
