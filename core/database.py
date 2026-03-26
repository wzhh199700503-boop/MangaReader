import sqlite3
import os
from loguru import logger
from common.config import cfg

class DatabaseManager:
    """ B.7 数据库服务 """

    def __init__(self):
        # 确保目录存在
        self.db_path = os.path.join(cfg.get(cfg.dataDir), "db", "manga_reader.db")
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._conn = None

    def get_connection(self):
        """ 获取数据库连接 (单例感) """
        if self._conn is None:
            self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
            # 开启 WAL 模式：支持高并发读写，防止“database is locked”
            self._conn.execute("PRAGMA journal_mode = WAL;")
            # 开启外键约束
            self._conn.execute("PRAGMA foreign_keys = ON;")
        return self._conn

    def init_db(self):
        """ 7.1 数据库初始化 (幂等) """
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            # 1.1 漫画表 (manga_id 为解析获取，设为主键)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS manga (
                    manga_id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    finished_date TEXT,
                    author TEXT,
                    intro TEXT,
                    rating REAL,
                    cover_online_path TEXT,
                    cover_local_path TEXT,
                    is_favorite INTEGER DEFAULT 0
                )
            ''')

            # 1.2 章节表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS chapters (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    manga_id TEXT,
                    chapter_order REAL,
                    FOREIGN KEY(manga_id) REFERENCES manga(manga_id) ON DELETE CASCADE
                )
            ''')

            # 1.3 图片表 (下载状态：-1=失效, 0=未下, 1=已下)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS images (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    manga_id TEXT,
                    chapter_id INTEGER,
                    image_order INTEGER,
                    online_path TEXT,
                    local_path TEXT,
                    download_status INTEGER DEFAULT 0,
                    FOREIGN KEY(chapter_id) REFERENCES chapters(id) ON DELETE CASCADE
                )
            ''')

            # 1.4 标签表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS tags (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tag_name TEXT UNIQUE NOT NULL
                )
            ''')

            # 1.5 漫画标签关联表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS manga_tags (
                    manga_id TEXT,
                    tag_id INTEGER,
                    PRIMARY KEY (manga_id, tag_id),
                    FOREIGN KEY(manga_id) REFERENCES manga(manga_id) ON DELETE CASCADE,
                    FOREIGN KEY(tag_id) REFERENCES tags(id) ON DELETE CASCADE
                )
            ''')

            # --- 性能补丁：建立索引 ---
            # 针对 900 万行图片数据，必须对查询频次最高的字段建索引
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_images_manga_id ON images(manga_id);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_images_chapter_id ON images(chapter_id);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_chapters_manga_id ON chapters(manga_id);")

            conn.commit()
            logger.info(f"数据库初始化成功: {self.db_path}")
        except Exception as e:
            conn.rollback()
            logger.error(f"数据库初始化失败: {e}")
            raise e
    # 在 DatabaseManager 类中添加以下方法
    def manga_exists(self, manga_id: str) -> bool:
        """ 7.5 通过漫画id判断是否存在 """
        conn = self.get_connection()
        cur = conn.execute("SELECT 1 FROM manga WHERE manga_id = ?", (manga_id,))
        return cur.fetchone() is not None

    def insert_manga_full_transaction(self, manga_info: dict, chapters: list, tags: list):
        """ 7.4 事务新增：一条漫画 + 若干章节 + 若干图片 + 标签关联 """
        conn = self.get_connection()
        cur = conn.cursor()
        try:
            # 1. 插入或忽略标签，获取标签ID
            tag_ids = []
            for tag_name in tags:
                cur.execute("INSERT OR IGNORE INTO tags (tag_name) VALUES (?)", (tag_name,))
                cur.execute("SELECT id FROM tags WHERE tag_name = ?", (tag_name,))
                tag_ids.append(cur.fetchone()[0])

            # 2. 插入漫画主表
            cur.execute('''
                INSERT INTO manga (manga_id, title, finished_date, author, intro, rating, cover_online_path, cover_local_path)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                manga_info['manga_id'], manga_info['title'], manga_info['release_date'],
                manga_info['author'], manga_info['description'], manga_info['rating'],
                manga_info['cover_url'], manga_info['cover_local_path']
            ))

            # 3. 关联标签
            for t_id in tag_ids:
                cur.execute("INSERT INTO manga_tags (manga_id, tag_id) VALUES (?, ?)", (manga_info['manga_id'], t_id))

            # 4. 插入章节与图片
            for chap in chapters:
                cur.execute('''
                    INSERT INTO chapters (title, manga_id, chapter_order)
                    VALUES (?, ?, ?)
                ''', (chap['title'], manga_info['manga_id'], chap['order']))
                chapter_id = cur.lastrowid

                # 插入该章节下的所有图片记录 (初始状态为 0)
                img_data = [(manga_info['manga_id'], chapter_id, img['order'], img['url']) for img in chap['images']]
                cur.executemany('''
                    INSERT INTO images (manga_id, chapter_id, image_order, online_path)
                    VALUES (?, ?, ?, ?)
                ''', img_data)

            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            logger.error(f"事务写入失败 | MangaID: {manga_info['manga_id']} | 错误: {e}")
            return False
    def update_image_status(self, m_id: str, c_id: int, order: int, status: int):
        """ 7.8 修改下载状态 (-1=失效, 0=未下, 1=已下) """
        conn = self.get_connection()
        try:
            conn.execute('''
                UPDATE images 
                SET download_status = ? 
                WHERE manga_id = ? AND chapter_id = ? AND image_order = ?
            ''', (status, m_id, c_id, order))
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            logger.error(f"更新图片状态失败 | 任务: {m_id}_{c_id}_{order} | 错误: {e}")
            return False
    def get_manga_list(self, page=1, limit=24, search="", tags=None, sort_desc=True, is_favorite=False):
        """ 分页获取漫画列表，支持搜索、标签过滤、排序和收藏筛选 """
        offset = (page - 1) * limit
        params = []
        sql = "SELECT manga_id, title, author, cover_local_path FROM manga WHERE 1=1"
        
        if is_favorite:
            sql += " AND is_favorite = 1"
            
        if search:
            sql += " AND title LIKE ?"
            params.append(f"%{search}%")
        
        if tags:
            placeholders = ','.join(['?'] * len(tags))
            sql += f" AND manga_id IN (SELECT manga_id FROM manga_tags WHERE tag_name IN ({placeholders}))"
            params.extend(tags)

        order = "DESC" if sort_desc else "ASC"
        # 假设你之前有个 update_time，如果没有可以用 finished_date 或 manga_id 排序
        sql += f" ORDER BY manga_id {order} LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        cursor = self.get_connection().execute(sql, params)
        return cursor.fetchall()

    def get_total_count(self, search="", tags=None, is_favorite=False):
        """ 真实获取总数，用于精准计算总页数 """
        params = []
        sql = "SELECT COUNT(1) FROM manga WHERE 1=1"
        
        if is_favorite:
            sql += " AND is_favorite = 1"
            
        if search:
            sql += " AND title LIKE ?"
            params.append(f"%{search}%")
            
        if tags:
            placeholders = ','.join(['?'] * len(tags))
            sql += f" AND manga_id IN (SELECT manga_id FROM manga_tags WHERE tag_name IN ({placeholders}))"
            params.extend(tags)
            
        cursor = self.get_connection().execute(sql, params)
        return cursor.fetchone()[0]

    def get_all_tags(self):
        """ 获取所有标签 """
        cursor = self.get_connection().execute("SELECT tag_name FROM tags")
        
        return [row[0] for row in cursor.fetchall()]

    def get_manga_detail(self, manga_id):
        """ 获取单部漫画详情 """
        cursor = self.get_connection().execute("SELECT * FROM manga WHERE manga_id=?", (manga_id,))
        return cursor.fetchone()
# 实例化单例
db_manager = DatabaseManager()