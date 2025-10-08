"""浏览器管理器 - 基于Playwright的浏览器池"""
import asyncio
from typing import Optional, List
from playwright.async_api import async_playwright, Browser, BrowserContext, Page, Playwright
from app.utils.anti_crawler import AntiCrawlerStrategy
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class BrowserManager:
    """浏览器管理器 - 管理浏览器实例和上下文"""

    def __init__(self, headless: bool = True, max_contexts: int = 3):
        """
        初始化浏览器管理器

        Args:
            headless: 是否无头模式
            max_contexts: 最大上下文数量（用于并发）
        """
        self.headless = headless
        self.max_contexts = max_contexts
        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        self.contexts: List[BrowserContext] = []

    async def start(self):
        """启动浏览器"""
        logger.info("启动浏览器...")
        self.playwright = await async_playwright().start()

        self.browser = await self.playwright.chromium.launch(
            headless=self.headless,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--no-sandbox',
                '--disable-dev-shm-usage'
            ]
        )

        logger.info(f"浏览器启动成功 (headless={self.headless})")

    async def create_context(self) -> BrowserContext:
        """
        创建新的浏览器上下文

        Returns:
            BrowserContext实例
        """
        if not self.browser:
            await self.start()

        context_options = AntiCrawlerStrategy.get_browser_context_options()
        context = await self.browser.new_context(**context_options)

        self.contexts.append(context)
        logger.info(f"创建新上下文，当前上下文数: {len(self.contexts)}")

        return context

    async def create_page(self, context: Optional[BrowserContext] = None) -> Page:
        """
        创建新页面

        Args:
            context: 指定上下文，如果为None则创建新上下文

        Returns:
            Page实例
        """
        if context is None:
            context = await self.create_context()

        page = await context.new_page()

        # 应用隐身模式
        await AntiCrawlerStrategy.stealth_mode(page)

        logger.info("创建新页面")
        return page

    async def close_context(self, context: BrowserContext):
        """关闭指定上下文"""
        await context.close()
        if context in self.contexts:
            self.contexts.remove(context)
        logger.info(f"关闭上下文，剩余上下文数: {len(self.contexts)}")

    async def close(self):
        """关闭所有资源"""
        logger.info("关闭浏览器管理器...")

        # 关闭所有上下文
        for context in self.contexts:
            await context.close()
        self.contexts.clear()

        # 关闭浏览器
        if self.browser:
            await self.browser.close()

        # 关闭playwright
        if self.playwright:
            await self.playwright.stop()

        logger.info("浏览器管理器已关闭")

    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器退出"""
        await self.close()


class BrowserPool:
    """浏览器池 - 用于并发任务"""

    def __init__(self, pool_size: int = 3, headless: bool = True):
        """
        初始化浏览器池

        Args:
            pool_size: 池大小
            headless: 是否无头模式
        """
        self.pool_size = pool_size
        self.headless = headless
        self.managers: List[BrowserManager] = []
        self.available: asyncio.Queue = asyncio.Queue()

    async def initialize(self):
        """初始化浏览器池"""
        logger.info(f"初始化浏览器池，大小: {self.pool_size}")

        for i in range(self.pool_size):
            manager = BrowserManager(headless=self.headless, max_contexts=1)
            await manager.start()
            self.managers.append(manager)
            await self.available.put(manager)

        logger.info("浏览器池初始化完成")

    async def acquire(self) -> BrowserManager:
        """获取可用的浏览器管理器"""
        manager = await self.available.get()
        logger.debug(f"获取浏览器管理器，剩余可用: {self.available.qsize()}")
        return manager

    async def release(self, manager: BrowserManager):
        """释放浏览器管理器"""
        await self.available.put(manager)
        logger.debug(f"释放浏览器管理器，剩余可用: {self.available.qsize()}")

    async def close_all(self):
        """关闭所有浏览器"""
        logger.info("关闭浏览器池...")
        for manager in self.managers:
            await manager.close()
        self.managers.clear()
        logger.info("浏览器池已关闭")
