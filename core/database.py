import aiosqlite
import os
import asyncio

class DBManager:
    def __init__(self, db_path="data/manga_reader.db"):
        self.db_path = db_path
        # 确保数据目录存在
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

    async def init_db(self):
        """初始化所有表结构"""
        if os.path.exists(self.db_path):
            return
        # 修正点：直接使用 aiosqlite.connect 作为上下文管理器
        async with aiosqlite.connect(self.db_path) as db:
            # 1. 配置连接（开启外键，设置 RowFactory）
            await db.execute("PRAGMA foreign_keys = ON")
            db.row_factory = aiosqlite.Row

            # 2. Manga 表
            await db.execute("""
                CREATE TABLE IF NOT EXISTS manga (
                    manga_id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    manga_url_path TEXT,
                    cover_url TEXT,
                    release_date TEXT,
                    list_remark TEXT,
                    author TEXT,
                    description TEXT,
                    rating REAL,
                    cache_status INTEGER DEFAULT 0,
                    is_favorite INTEGER DEFAULT 0
                )
            """)

            # 3. Chapters 表
            await db.execute("""
                CREATE TABLE IF NOT EXISTS chapters (
                    chapter_id TEXT PRIMARY KEY,  -- 修改点：INTEGER 改为 TEXT，去掉 AUTOINCREMENT
                    manga_id TEXT,      
                    chapter_name TEXT,
                    chapter_path TEXT,
                    sort_index INTEGER,
                    FOREIGN KEY (manga_id) REFERENCES manga (manga_id) ON DELETE CASCADE
                )
            """)

            # 4. History 表
            await db.execute("""
                CREATE TABLE IF NOT EXISTS history (
                    manga_id TEXT PRIMARY KEY,
                    chapter_id TEXT,
                    page_index INTEGER DEFAULT 0,
                    last_read_time INTEGER,
                    FOREIGN KEY (manga_id) REFERENCES manga (manga_id) ON DELETE CASCADE,
                    FOREIGN KEY (chapter_id) REFERENCES chapters (chapter_id) ON DELETE SET NULL
                )
            """)

            # 5. Images 表
            await db.execute("""
                CREATE TABLE IF NOT EXISTS images (
                    image_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    manga_id TEXT,
                    chapter_id TEXT,
                    image_url TEXT,
                    local_path TEXT,
                    page_index INTEGER,
                    download_status INTEGER DEFAULT 0,
                    FOREIGN KEY (manga_id) REFERENCES manga (manga_id) ON DELETE CASCADE,
                    FOREIGN KEY (chapter_id) REFERENCES chapters (chapter_id) ON DELETE CASCADE
                )
            """)

            await db.commit()
            print(f"数据库初始化成功: {os.path.abspath(self.db_path)}")
            
    async def check_manga_exists(self, manga_id: str) -> bool:
        """快速检查漫画是否在库"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT 1 FROM manga WHERE manga_id = ?", (manga_id,)) as cursor:
                return await cursor.fetchone() is not None

    async def save_full_manga_data(self, basic, detail):
        """原子化保存：列表数据 + 详情数据 + 章节列表"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("PRAGMA foreign_keys = ON")
            
            # 1. 存主表
            await db.execute("""
                INSERT OR REPLACE INTO manga (
                    manga_id, title, manga_url_path, cover_url, release_date, 
                    list_remark, author, description, rating
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                basic["manga_id"], basic["title"], basic["manga_url_path"],
                basic["cover_url"], basic["release_date"], basic["list_remark"],
                detail["author"], detail["description"], detail["rating"]
            ))

            # 2. 存章节 (使用 executemany 提高效率)
            chapter_tasks = [
                (f"{basic['manga_id']}_{c['chapter_path']}", basic['manga_id'], 
                 c['chapter_name'], c['chapter_path'], c['sort_index'])
                for c in detail["chapters"]
            ]
            await db.executemany("""
                INSERT OR IGNORE INTO chapters (
                    chapter_id, manga_id, chapter_name, chapter_path, sort_index
                ) VALUES (?, ?, ?, ?, ?)
            """, chapter_tasks)
            
            await db.commit()
async def test():
    manager = DBManager()
    await manager.init_db()

if __name__ == "__main__":
    asyncio.run(test())