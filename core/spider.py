import httpx
from bs4 import BeautifulSoup
import re
from typing import Dict, Any

class MangaSpider:
    def __init__(self):
        # 修正：基础 URL 加上协议
        self.base_url = "https://hmjd8.com"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Referer": self.base_url,
            "Accept-Language": "zh-CN,zh;q=0.9",
        }

    async def fetch_list_page(self, page_num: int) -> Dict[str, Any]:
        """抓取列表页并增加错误检查"""
        # 修正 URL 拼接逻辑：如果是第一页，尝试直接访问基准路径
        url = f"{self.base_url}/manhua/all/ob/time/st/completed"
        if page_num > 1:
            url = f"{url}/page/{page_num}"

        print(f"正在请求: {url}")

        async with httpx.AsyncClient(headers=self.headers, timeout=15, follow_redirects=True) as client:
            try:
                resp = await client.get(url)
                
                # 检查状态码
                if resp.status_code != 200:
                    print(f"请求失败！状态码: {resp.status_code}")
                    # 如果被封了，打印前 200 个字符看看是什么内容（比如 Cloudflare 拦截页）
                    print(f"响应内容片段: {resp.text[:200]}")
                    return {"total_pages": 0, "mangas": []}

                soup = BeautifulSoup(resp.text, "html.parser")
                
                # 核心：增加对总页数标签的判断
                page_total_tag = soup.find("div", class_="hl-page-total")
                if not page_total_tag:
                    print("警告：未能在页面中找到 'hl-page-total' 标签。")
                    # 调试：把整个 HTML 存下来看看
                    # with open("debug.html", "w", encoding="utf-8") as f: f.write(resp.text)
                    return {"total_pages": 0, "mangas": []}

                page_text = page_total_tag.get_text() # "1 / 78页"
                match = re.search(r"/\s*(\d+)\s*页", page_text)
                total_pages = int(match.group(1)) if match else 1
                
                # 解析漫画列表
                items = soup.find_all("li", class_="hl-list-item")
                mangas = []
                
                for item in items:
                    a_thumb = item.find("a", class_="hl-item-thumb")
                    if not a_thumb: continue
                    
                    href = a_thumb.get("href")
                    # 匹配 ID
                    m_id_match = re.search(r"manhua-(\d+)", href)
                    m_id = m_id_match.group(1) if m_id_match else href
                    
                    mangas.append({
                        "manga_id": m_id,
                        "title": a_thumb.get("title", "未知"),
                        "manga_url_path": href,
                        "cover_url": a_thumb.get("data-original", ""),
                        "release_date": item.find("div", class_="hl-item-sub").get_text(strip=True),
                        "list_remark": item.find("span", class_="remarks").get_text(strip=True) if item.find("span", class_="remarks") else ""
                    })
                
                return {"total_pages": total_pages, "mangas": mangas}

            except Exception as e:
                print(f"发生网络异常: {e}")
                return {"total_pages": 0, "mangas": []}

    async def fetch_detail(self, url_path: str) -> Dict[str, Any]:
        """
        爬取详情页
        返回: { "author": str, "description": str, "rating": float, "chapters": List[Dict] }
        """
        url = f"{self.base_url}{url_path}"
        
        async with httpx.AsyncClient(headers=self.headers, timeout=10) as client:
            resp = await client.get(url)
            soup = BeautifulSoup(resp.text, "html.parser")
            
            # 1. 评分 (5.6)
            rating_text = soup.find("div", class_="hl-score-nums").find("span").get_text()
            
            # 2. 详情内容区 (处理作者、TAG、简介)
            # 我们直接从 hl-data-xs 获取，这里比较集中
            data_xs = soup.find("div", class_="hl-data-xs")
            
            # 作者解析
            author_tag = data_xs.find("a", href=re.compile(r"/search/"))
            author = author_tag.get_text(strip=True) if author_tag else "未知"
            
            # 简介解析 (提取“简介：”后面的文本)
            # 在 hl-vod-data 的 blurb 类里有完整简介
            desc_item = soup.find("li", class_="blurb")
            description = desc_item.get_text().replace("简介：", "").strip() if desc_item else ""

            # 3. 章节解析
            chapter_list = soup.find("ul", id="hl-plays-list").find_all("li")
            total_chapters = len(chapter_list)
            chapters = []
            
            for i, li in enumerate(chapter_list):
                a_tag = li.find("a")
                c_href = a_tag.get("href") # "/manhua-2406/WFbelf4ktMjrADiU.html"
                
                # 提取章节唯一路径 (WFbelf4ktMjrADiU)
                c_path = c_href.split("/")[-1].replace(".html", "")
                
                chapters.append({
                    "chapter_name": a_tag.get("title").replace(f"{a_tag.get_text()} - ", "").strip(),
                    "chapter_path": c_path,
                    "sort_index": total_chapters - i # 逆序排序逻辑
                })
                
            return {
                "author": author,
                "description": description,
                "rating": float(rating_text),
                "chapters": chapters
            }

if __name__ == "__main__":
    import asyncio
    async def test():
        s = MangaSpider()
        # 测试列表页
        print("测试列表页...")
        list_res = await s.fetch_list_page(1)
        print(f"总页数: {list_res['total_pages']}")
        print(f"第一部漫画: {list_res['mangas'][0]}")
        
        # 测试详情页 (以黑道千金为例)
        print("\n测试详情页...")
        detail_res = await s.fetch_detail("/manhua-2406.html")
        print(f"作者: {detail_res['author']}")
        print(f"评分: {detail_res['rating']}")
        print(f"第一话: {detail_res['chapters'][-1]}") # 取列表最后一个

    asyncio.run(test())