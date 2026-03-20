import flet as ft
import asyncio
from core.database import DBManager
from core.spider import MangaSpider
from core.sync_manager import SyncManager
from core.config_manager import ConfigManager
from core.logger_manager import logger
from ui.views.loading_view import LoadingView

async def main(page: ft.Page):
    # 1. 窗口基础设置
    page.title = "Manga Reader - 极致本地镜像"
    page.window.width = 1000
    page.window.height = 750
    page.window.min_width = 800
    page.window.min_height = 600
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 0  # 让加载页无边距占满窗口
    
    # 2. 基础设施初始化
    # 注意：ConfigManager 是单例，Logger 已经全局初始化
    conf = ConfigManager()
    db = DBManager()
    spider = MangaSpider()
    sync_manager = SyncManager(db, spider)

    logger.info("MangaReader 启动中...")

    # 3. 定义同步完成后的界面切换逻辑
    async def show_home_view():
        """
        同步完成后，清理加载页，显示主界面
        """
        logger.info("准备进入主界面...")
        page.controls.clear()
        
        # 暂时先放一个占位符，等下一阶段开发 HomeView 列表
        page.add(
            ft.Container(
                content=ft.Column(
                    [
                        ft.Icon("check_circle", size=80, color="green"),
                        ft.Text("同步完成！", size=30, weight="bold"),
                        ft.Text("本地数据库已准备就绪，开始你的漫画之旅吧。", size=16, color="grey"),
                        ft.ElevatedButton("进入库", icon="explore")
                    ],
                    horizontal_alignment="center",
                    alignment="center",
                ),
                expand=True,
                alignment=ft.alignment.center,
            )
        )
        page.update()

    # 4. 渲染加载界面
    loading_view = LoadingView()
    page.add(loading_view)
    page.update()

    # 5. 启动后台同步逻辑
    try:
        # 将 loading_view 的进度更新函数作为回调传入
        # SyncManager 会根据全量/增量逻辑自动运行
        await sync_manager.run_sync(loading_view.update_progress)
        
        # 任务执行完后，跳转到主页
        await show_home_view()
        
    except Exception as e:
        logger.error(f"启动同步任务时发生致命错误: {e}")
        # 如果报错，在 UI 上给个提示
        loading_view.status_text.value = f"同步出错: {str(e)}"
        loading_view.progress_bar.color = "red"
        page.update()

if __name__ == "__main__":
    # 启动 Flet App
    try:
        ft.run(main)
    except Exception as e:
        print(f"程序运行崩溃: {e}")