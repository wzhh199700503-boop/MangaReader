import re
from bs4 import BeautifulSoup
from loguru import logger
from core.request_client import request_client

class SpiderService:
    """ B.6 爬虫服务 (集成重试机制与 lxml) """

    def __init__(self):
        self.base_url = "https://hmjd8.com"
        # 预编译正则提高性能
        self.re_total_pages = re.compile(r"/\s*(\d+)\s*页")
        self.re_manga_id = re.compile(r"manhua-(\d+)")

    def _get_soup(self, url):
        """ 内部工具：获取 BeautifulSoup 对象 """
        resp = request_client.get(url)
        if resp and resp.status_code == 200:
            return BeautifulSoup(resp.content, "lxml")
        return None

    def fetch_stats(self) -> dict:
        """ 6.4 爬取总页数, 总漫画数 """
        url = f"{self.base_url}/manhua/all/ob/time/st/completed"
        soup = self._get_soup(url)
        stats = {"total_pages": 1, "total_manga": 0}
        
        if soup:
            count_tag = soup.select_one("span.hl-rb-total em.hl-total")
            if count_tag:
                stats["total_manga"] = int(count_tag.get_text())
            
            page_tag = soup.find("div", class_="hl-page-total")
            if page_tag:
                match = self.re_total_pages.search(page_tag.get_text())
                if match:
                    stats["total_pages"] = int(match.group(1))
                    
        return stats

    def fetch_manga_list(self, page_num: int) -> list:
        """ 6.1 爬取漫画列表 """
        url = f"{self.base_url}/manhua/all/ob/time/st/completed"
        if page_num > 1:
            url = f"{url}/page/{page_num}"
        
        soup = self._get_soup(url)
        mangas = []
        if not soup: return mangas

        items = soup.find_all("li", class_="hl-list-item")
        for item in items:
            a_thumb = item.find("a", class_="hl-item-thumb")
            if not a_thumb: continue

            href = a_thumb.get("href", "")
            m_id_match = self.re_manga_id.search(href)
            m_id = m_id_match.group(1) if m_id_match else href

            mangas.append({
                "manga_id": m_id,
                "title": a_thumb.get("title", "未知"),
                "cover_url": a_thumb.get("data-original", ""),
                "release_date": item.find("div", class_="hl-item-sub").get_text(strip=True),
                "detail_path": href 
            })
        return mangas

    def fetch_detail(self, detail_path: str) -> dict:
        """ 6.2 爬取漫画详情与章节列表 (支持标签解析) """
        url = f"{self.base_url}{detail_path}"
        soup = self._get_soup(url)
        if not soup: return {}

        # 1. 解析作者 (通过 href 包含 search 的特征点)
        author_tag = soup.select_one("div.hl-data-xs a[href*='/search/']")
        author = author_tag.get_text(strip=True) if author_tag else "未知"

        # 2. 解析标签 (精准匹配 em 中的 TAG 文字)
        tags = []
        tag_label = soup.find("em", string=lambda x: x and "TAG" in x)
        if tag_label:
            # 找到 em 的父级 li，并提取其中所有的 a 标签文字
            tags = [a.get_text(strip=True) for a in tag_label.parent.find_all("a")]
        
        # 3. 解析简介
        desc_item = soup.find("li", class_="blurb")
        description = desc_item.get_text().replace("简介：", "").strip() if desc_item else ""

        # 4. 解析章节 (逆序处理)
        chapter_list = soup.find("ul", id="hl-plays-list").find_all("li")
        chapters_raw = []
        for li in chapter_list:
            a_tag = li.find("a")
            chapters_raw.append({
                "title": a_tag.get("title", "").replace(f"{a_tag.get_text()} - ", "").strip(),
                "read_path": a_tag.get("href"),
            })

        chapters_sorted = chapters_raw[::-1]
        for i, chapter in enumerate(chapters_sorted):
            chapter["order"] = i + 1

        return {
            "author": author,
            "tags": tags, # 包含：正妹, 恋爱, 浪漫等
            "description": description,
            "rating": float(soup.select_one("div.hl-score-nums span").get_text() or 0),
            "chapters": chapters_sorted
        }

    def fetch_reading_images(self, read_path: str) -> list:
        """ 6.3 爬取阅读页图片链接 """
        url = f"{self.base_url}{read_path}"
        soup = self._get_soup(url)
        images = []
        if not soup: return images

        img_tags = soup.select("img.hl-lazy")
        for i, img in enumerate(img_tags):
            src = img.get("data-original") or img.get("data-src") or img.get("src")
            if src:
                # 补全协议
                if src.startswith("//"): src = "https:" + src
                images.append({
                    "url": src,
                    "order": i + 1
                })
        return images

spider_service = SpiderService()