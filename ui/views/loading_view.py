import flet as ft

class LoadingView(ft.Container):
    def __init__(self):
        super().__init__()
        self.expand = True  
        self.alignment = ft.Alignment(0, 0)  
        # 修正：直接使用字符串 "black12"
        self.bgcolor = "black12" 

        # 1. 进度描述文字
        self.status_text = ft.Text(
            value="准备开始同步...",
            size=16,
            weight="w400",  # 修正：使用字符串 "w400"
            text_align="center" # 修正：使用字符串 "center"
        )

        # 2. 进度条
        self.progress_bar = ft.ProgressBar(
            width=500,
            height=8,
            color="blueAccent", # 修正：使用字符串
            bgcolor="grey900",   # 修正：使用字符串
            value=0  
        )

        # 3. 布局组装
        self.content = ft.Column(
            controls=[
                self.status_text,
                ft.Container(height=10), 
                self.progress_bar,
            ],
            tight=True, 
            horizontal_alignment="center", # 修正：直接用 "center"
        )

    def update_progress(self, current: int, total: int, title: str):
        # 标题截断逻辑
        display_title = (title[:10] + "...") if len(title) > 10 else title
        
        # 更新文字
        self.status_text.value = f"当前爬取第 {current} 部漫画, 标题: {display_title}, 共 {total} 部"
        
        # 更新进度条
        self.progress_bar.value = current / total if total > 0 else 0
        
        self.update()