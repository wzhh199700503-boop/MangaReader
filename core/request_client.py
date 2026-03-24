import requests
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
from loguru import logger
from common.config import cfg

class RequestClient:
    """ B.4 带有重试机制的请求封装 """

    def __init__(self):
        self.session = requests.Session()
        
        # 配置默认请求头，模拟浏览器避免被基础反爬拦截
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": "https://www.google.com" # 部分图片服务器校验 Referer
        })

        # 从配置中读取重试次数
        retry_count = cfg.get(cfg.retryCount)
        
        # 定义重试策略
        # backoff_factor: 重试间隔会以 0.3s, 0.6s, 1.2s ... 指数级增长
        # status_forcelist: 遇到这些状态码时强制重试
        retries = Retry(
            total=retry_count,
            backoff_factor=0.3,
            status_forcelist=[500, 502, 503, 504],
            raise_on_status=False
        )

        # 将重试策略挂载到 http 和 https 协议上
        adapter = HTTPAdapter(max_retries=retries)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    def get(self, url, timeout=10, **kwargs):
        """ 封装 GET 请求 """
        try:
            response = self.session.get(url, timeout=timeout, **kwargs)
            # 如果不是 200，记录一下日志但先不抛异常，交给上层逻辑处理 404
            if response.status_code != 200:
                logger.warning(f"请求失败 | 状态码: {response.status_code} | URL: {url}")
            return response
        except requests.exceptions.RequestException as e:
            logger.error(f"网络异常 | 错误: {e} | URL: {url}")
            return None

# 单例模式，全局复用 Session 提高性能
request_client = RequestClient()