"""基础爬虫类"""
from abc import ABC, abstractmethod
from typing import Optional
from playwright.async_api import Page, BrowserContext
from app.core.browser_manager import BrowserManager
from app.utils.anti_crawler import AntiCrawlerStrategy
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class BaseScraper(ABC):
    """基础爬虫抽象类"""

    def __init__(self, browser_manager: BrowserManager):
        """
        初始化爬虫

        Args:
            browser_manager: 浏览器管理器
        """
        self.browser_manager = browser_manager
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None

    async def setup(self):
        """设置爬虫（创建上下文和页面）"""
        logger.info(f"设置 {self.__class__.__name__}")
        self.page = await self.browser_manager.create_page()

    async def teardown(self):
        """清理资源"""
        logger.info(f"清理 {self.__class__.__name__}")
        if self.page:
            await self.page.close()

    async def navigate(self, url: str, wait_until: str = "domcontentloaded"):
        """
        导航到URL

        Args:
            url: 目标URL
            wait_until: 等待条件
        """
        logger.info(f"导航至: {url}")
        await self.page.goto(url, wait_until=wait_until, timeout=30000)
        await AntiCrawlerStrategy.random_delay(1000, 2000)

    async def safe_click(self, selector: str, timeout: int = 5000):
        """
        安全点击元素

        Args:
            selector: CSS选择器
            timeout: 超时时间
        """
        try:
            await self.page.wait_for_selector(selector, timeout=timeout)
            await self.page.click(selector)
            await AntiCrawlerStrategy.random_delay(500, 1500)
            logger.debug(f"点击元素: {selector}")
        except Exception as e:
            logger.warning(f"点击元素失败 {selector}: {e}")

    async def safe_type(self, selector: str, text: str, timeout: int = 5000):
        """
        安全输入文本

        Args:
            selector: CSS选择器
            text: 输入文本
            timeout: 超时时间
        """
        try:
            await self.page.wait_for_selector(selector, timeout=timeout)
            await self.page.fill(selector, text)
            await AntiCrawlerStrategy.random_delay(500, 1000)
            logger.debug(f"输入文本到 {selector}: {text}")
        except Exception as e:
            logger.warning(f"输入文本失败 {selector}: {e}")

    async def scroll_to_bottom(self, scroll_count: int = 3):
        """滚动到页面底部"""
        await AntiCrawlerStrategy.human_like_scroll(self.page, scroll_count)

    async def wait_for_network_idle(self, timeout: int = 10000):
        """等待网络空闲"""
        try:
            await self.page.wait_for_load_state("networkidle", timeout=timeout)
        except Exception as e:
            logger.warning(f"等待网络空闲超时: {e}")

    @abstractmethod
    async def scrape(self, *args, **kwargs):
        """抽象方法：执行爬取任务"""
        pass

    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self.setup()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器退出"""
        await self.teardown()
