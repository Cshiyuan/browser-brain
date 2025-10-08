"""基于Browser-Use的小红书AI爬虫"""
import asyncio
from typing import List
from pydantic import BaseModel, Field
from app.scrapers.browser_use_scraper import BrowserUseScraper
from app.models.attraction import XHSNote
from app.utils.logger import setup_logger, log_function_call, log_step
from datetime import datetime

logger = setup_logger(__name__)


# 定义小红书笔记的结构化输出模型
class XHSNoteOutput(BaseModel):
    """单条小红书笔记输出"""
    title: str = Field(description="笔记标题")
    author: str = Field(description="作者名称")
    content: str = Field(description="笔记正文内容")
    likes: int = Field(default=0, description="点赞数")
    collects: int = Field(default=0, description="收藏数")
    comments: int = Field(default=0, description="评论数")
    extracted_links: List[str] = Field(default_factory=list, description="提取的URL链接（官网、预订链接等）")
    keywords: List[str] = Field(default_factory=list, description="关键词（官网、预订、门票等）")
    images: List[str] = Field(default_factory=list, description="图片URL列表")


class XHSNotesCollection(BaseModel):
    """小红书笔记集合"""
    notes: List[XHSNoteOutput] = Field(description="笔记列表")


class XHSScraper(BrowserUseScraper):
    """基于Browser-Use的小红书AI爬虫"""

    async def _handle_captcha_manual(self, wait_seconds: int = 60):
        """
        验证码人工处理：暂停等待用户手动完成验证

        Args:
            wait_seconds: 等待时间（秒），默认60秒
        """
        logger.warning("⚠️  检测到验证码，暂停等待人工处理...")
        logger.info("📌 请在浏览器窗口中完成验证码验证")
        logger.info(f"⏳ 系统将在 {wait_seconds} 秒后自动继续...")

        # 每10秒提示一次剩余时间
        for remaining in range(wait_seconds, 0, -10):
            logger.info(f"⏱️  剩余等待时间: {remaining} 秒")
            await asyncio.sleep(min(10, remaining))

        logger.info("✅ 等待结束，继续执行任务...")

    @log_function_call
    async def search_attraction(self, attraction_name: str, max_notes: int = 5) -> List[XHSNote]:
        """
        使用AI搜索景点相关笔记

        Args:
            attraction_name: 景点名称
            max_notes: 最大笔记数量

        Returns:
            小红书笔记列表
        """
        logger.info(f"========== 开始小红书爬取 ==========")
        logger.info(f"目标景点: {attraction_name}, 目标笔记数: {max_notes}")
        log_step(1, "准备小红书搜索任务", attraction=attraction_name, max_notes=max_notes)

        # 构建AI任务描述
        task = f"""
任务：在小红书搜索"{attraction_name}"相关的旅游笔记

具体步骤：
1. 访问小红书网站 https://www.xiaohongshu.com
2. 等待页面完全加载(3-5秒)
3. 在搜索框中输入关键词："{attraction_name}"
4. 点击搜索或按回车键
5. 等待搜索结果加载完成
6. 浏览搜索结果，找到前{max_notes}篇相关笔记
7. 对于每篇笔记，提取以下信息：
   - 笔记标题
   - 作者名称
   - 笔记正文内容（尽可能完整）
   - 点赞数、收藏数、评论数
   - 笔记中的图片URL（前3张）
   - 提取笔记中提到的URL链接（特别是官网、预订、门票相关链接）
   - 识别关键词（如：官网、官方网站、预订、门票、开放时间等）

重要提示：
- 像真实用户一样操作，每步之间留有间隔
- 优先选择点赞数和收藏数较高的笔记
- 如果遇到任何弹窗或引导，先关闭它们
- 如果遇到登录要求，点击"稍后再说"或关闭按钮
- 遇到验证码时，暂停并等待人工处理
- 返回结构化的JSON数据
"""

        # 使用AI执行爬取
        log_step(2, "调用Browser-Use AI执行小红书爬取")
        result = await self.scrape_with_task(
            task=task,
            output_model=XHSNotesCollection,
            max_steps=30  # 小红书需要多步操作
        )

        # 检测是否遇到验证码
        if result["status"] == "success" and result.get("urls"):
            visited_urls = result["urls"]
            # 检查是否访问了验证码页面
            if any("captcha" in url.lower() for url in visited_urls):
                logger.warning("🚫 检测到访问了验证码页面，启动人工处理流程...")

                # 暂停等待人工处理
                await self._handle_captcha_manual(wait_seconds=60)

                # 重新尝试执行任务
                logger.info("🔄 重新尝试执行爬取任务...")
                result = await self.scrape_with_task(
                    task=task,
                    output_model=XHSNotesCollection,
                    max_steps=30
                )

        log_step(3, "处理AI返回结果", status=result["status"])

        if result["status"] != "success":
            logger.error(f"❌ AI爬取小红书失败: {result.get('error', 'Unknown error')}")
            logger.error(f"执行步骤数: {result.get('steps', 0)}, 访问的URL: {result.get('urls', [])}")
            return []

        # 转换为XHSNote对象
        notes_data = result["data"]
        xhs_notes = []

        # 处理 AI Agent 失败返回字符串或无数据的情况
        if isinstance(notes_data, str) or not hasattr(notes_data, 'notes'):
            logger.warning(f"⚠️  AI返回数据格式异常或无数据: {type(notes_data)}")
            logger.debug(f"原始返回数据: {notes_data}")
            return []

        logger.info(f"AI成功返回 {len(notes_data.notes)} 篇笔记数据")
        log_step(4, "转换笔记数据为XHSNote对象", note_count=len(notes_data.notes))

        for idx, note_output in enumerate(notes_data.notes):
            note = XHSNote(
                note_id=f"xhs_{attraction_name}_{idx}",
                title=note_output.title,
                author=note_output.author,
                content=note_output.content,
                likes=note_output.likes,
                collects=note_output.collects,
                comments=note_output.comments,
                images=note_output.images[:5],  # 最多5张图片
                extracted_links=note_output.extracted_links,
                keywords=note_output.keywords,
                created_at=datetime.now()
            )
            xhs_notes.append(note)
            logger.debug(f"笔记 {idx+1}: {note.title[:30]}... (点赞:{note.likes}, 收藏:{note.collects})")

        logger.info(f"✅ 成功爬取 {len(xhs_notes)} 篇小红书笔记")
        logger.info(f"========== 小红书爬取完成 ==========")
        return xhs_notes

    async def scrape(self, attraction_name: str, max_notes: int = 10) -> List[XHSNote]:
        """
        实现基类的抽象方法

        Args:
            attraction_name: 景点名称
            max_notes: 最大笔记数

        Returns:
            笔记列表
        """
        return await self.search_attraction(attraction_name, max_notes)
