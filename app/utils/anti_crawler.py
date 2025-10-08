"""反爬虫策略工具"""
import random
import asyncio
from typing import List, Optional


class AntiCrawlerStrategy:
    """反爬虫策略"""

    # User-Agent池
    USER_AGENTS = [
        # Chrome
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        # Firefox
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 14.1; rv:121.0) Gecko/20100101 Firefox/121.0",
        # Edge
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
        # Safari
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_1_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15"
    ]

    @classmethod
    def get_random_user_agent(cls) -> str:
        """获取随机User-Agent"""
        return random.choice(cls.USER_AGENTS)

    @classmethod
    async def random_delay(cls, min_ms: int = 1000, max_ms: int = 3000):
        """
        随机延迟

        Args:
            min_ms: 最小延迟（毫秒）
            max_ms: 最大延迟（毫秒）
        """
        delay = random.randint(min_ms, max_ms) / 1000
        await asyncio.sleep(delay)

    @classmethod
    async def human_like_scroll(cls, page, scroll_count: int = 3):
        """
        模拟人类滚动行为

        Args:
            page: Playwright page对象
            scroll_count: 滚动次数
        """
        for _ in range(scroll_count):
            # 随机滚动距离
            scroll_distance = random.randint(300, 800)
            await page.evaluate(f"window.scrollBy(0, {scroll_distance})")
            await cls.random_delay(500, 1500)

    @classmethod
    async def human_like_mouse_move(cls, page):
        """模拟鼠标移动"""
        width = await page.evaluate("window.innerWidth")
        height = await page.evaluate("window.innerHeight")

        x = random.randint(0, width)
        y = random.randint(0, height)

        await page.mouse.move(x, y)

    @classmethod
    def get_browser_context_options(cls) -> dict:
        """
        获取浏览器上下文配置

        Returns:
            Playwright context配置
        """
        return {
            "user_agent": cls.get_random_user_agent(),
            "viewport": {"width": 1920, "height": 1080},
            "locale": "zh-CN",
            "timezone_id": "Asia/Shanghai",
            # 添加常见权限
            "permissions": ["geolocation"],
            # 禁用自动化检测特征
            "java_script_enabled": True,
            # 额外header
            "extra_http_headers": {
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
            }
        }

    @classmethod
    async def stealth_mode(cls, page):
        """
        隐藏Playwright自动化特征

        Args:
            page: Playwright page对象
        """
        # 覆盖navigator.webdriver
        await page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)

        # 覆盖chrome对象
        await page.add_init_script("""
            window.chrome = {
                runtime: {}
            };
        """)

        # 覆盖permissions
        await page.add_init_script("""
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
            );
        """)

        # 覆盖plugins
        await page.add_init_script("""
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });
        """)
