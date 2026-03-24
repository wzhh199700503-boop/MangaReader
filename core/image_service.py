import os
from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot
from loguru import logger
from common.config import cfg
from core.download_service import download_service

class ImageService(QObject):
    """ B.3 章节图片服务 """
    
    # 信号：(manga_id, chapter_id, image_order, local_path)
    imageReady = pyqtSignal(str, int, int, str)

    def __init__(self):
        super().__init__()
        # 建立与下载服务的联动：当下号一张图，尝试通知 UI
        download_service.signals.finished.connect(self._on_download_finished)

    def get_image(self, manga_id, chapter_id, image_order, url):
        """ 
        UI 调用此方法请求图片。
        逻辑：本地有就直接发信号；没有就触发异步下载。
        """
        # 1. 构造物理路径 (C.2.3: 补零逻辑)
        ext = url.split('.')[-1] if '.' in url else 'webp'
        file_name = f"{image_order:03d}.{ext}"
        local_path = os.path.join(
            cfg.get(cfg.dataDir), 
            str(manga_id), 
            str(chapter_id), 
            file_name
        )

        # 2. 检查物理文件是否存在
        if os.path.exists(local_path):
            logger.debug(f"命中本地缓存: {manga_id}/{chapter_id}/{image_order}")
            self.imageReady.emit(str(manga_id), int(chapter_id), int(image_order), local_path)
            return True

        # 3. 本地无图，触发异步下载
        # download_image 内部有去重机制，不会重复创建任务
        download_service.download_image(manga_id, chapter_id, image_order, url, ext)
        return False

    @pyqtSlot(str, int, int, bool, str)
    def _on_download_finished(self, m_id, c_id, i_order, success, path):
        """ 下载服务完成后的回掉 """
        if success:
            # 下载成功，通知 UI 图片已就绪
            self.imageReady.emit(m_id, c_id, i_order, path)
        else:
            logger.warning(f"图片就绪失败 | 任务: {m_id}_{c_id}_{i_order}")

# 实例化单例
image_service = ImageService()