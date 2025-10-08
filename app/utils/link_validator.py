"""URL链接验证和提取工具"""
import re
from typing import List, Tuple, Optional
from urllib.parse import urlparse
import asyncio
from playwright.async_api import async_playwright


class LinkValidator:
    """链接验证器"""

    # 官网相关关键词
    OFFICIAL_KEYWORDS = [
        "官网", "官方网站", "official", "website",
        "官方", "景区官网", "博物馆官网"
    ]

    # 常见顶级域名权重
    DOMAIN_WEIGHTS = {
        ".gov.cn": 1.0,
        ".org.cn": 0.9,
        ".gov": 1.0,
        ".org": 0.8,
        ".com.cn": 0.7,
        ".cn": 0.6,
        ".com": 0.5
    }

    @staticmethod
    def extract_urls(text: str) -> List[str]:
        """
        从文本中提取URL

        Args:
            text: 待提取文本

        Returns:
            URL列表
        """
        # 匹配http/https链接
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        urls = re.findall(url_pattern, text)

        # 匹配www开头的链接
        www_pattern = r'www\.[^\s<>"{}|\\^`\[\]]+'
        www_urls = re.findall(www_pattern, text)
        www_urls = [f"https://{url}" for url in www_urls]

        # 去重
        all_urls = list(set(urls + www_urls))

        return all_urls

    @staticmethod
    def extract_keywords(text: str, keywords: List[str]) -> List[str]:
        """
        提取文本中的关键词

        Args:
            text: 待提取文本
            keywords: 关键词列表

        Returns:
            匹配到的关键词
        """
        found = []
        for keyword in keywords:
            if keyword in text:
                found.append(keyword)
        return found

    @classmethod
    def score_url_relevance(cls, url: str, context: str, attraction_name: str) -> float:
        """
        评估URL与景点的相关性

        Args:
            url: 待评估URL
            context: URL所在的上下文
            attraction_name: 景点名称

        Returns:
            相关性分数 (0-1)
        """
        score = 0.0

        # 1. 检查域名权重
        for domain, weight in cls.DOMAIN_WEIGHTS.items():
            if url.endswith(domain):
                score += weight * 0.4
                break

        # 2. 检查URL中是否包含景点名称拼音或英文
        parsed = urlparse(url)
        domain_name = parsed.netloc.lower()

        # 简单匹配景点名称（实际应该用拼音转换库）
        if attraction_name in domain_name:
            score += 0.3

        # 3. 检查上下文关键词
        official_keywords_found = cls.extract_keywords(context, cls.OFFICIAL_KEYWORDS)
        if official_keywords_found:
            score += 0.3

        return min(score, 1.0)

    @classmethod
    async def validate_url(cls, url: str, timeout: int = 10000) -> Tuple[bool, Optional[str]]:
        """
        验证URL是否可访问

        Args:
            url: 待验证URL
            timeout: 超时时间（毫秒）

        Returns:
            (是否可访问, 最终URL或错误信息)
        """
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context()
                page = await context.new_page()

                response = await page.goto(url, timeout=timeout, wait_until="domcontentloaded")

                if response and response.ok:
                    final_url = page.url
                    await browser.close()
                    return True, final_url
                else:
                    await browser.close()
                    return False, f"HTTP {response.status if response else 'No response'}"

        except Exception as e:
            return False, str(e)

    @classmethod
    def filter_and_rank_urls(
        cls,
        text: str,
        attraction_name: str,
        min_score: float = 0.5
    ) -> List[Tuple[str, float]]:
        """
        从文本中提取URL并按相关性排序

        Args:
            text: 文本内容
            attraction_name: 景点名称
            min_score: 最低分数阈值

        Returns:
            [(url, score), ...] 按分数降序排列
        """
        urls = cls.extract_urls(text)

        # 评分
        scored_urls = []
        for url in urls:
            # 获取URL周围的上下文（前后100字符）
            idx = text.find(url)
            start = max(0, idx - 100)
            end = min(len(text), idx + len(url) + 100)
            context = text[start:end]

            score = cls.score_url_relevance(url, context, attraction_name)

            if score >= min_score:
                scored_urls.append((url, score))

        # 按分数降序排序
        scored_urls.sort(key=lambda x: x[1], reverse=True)

        return scored_urls
