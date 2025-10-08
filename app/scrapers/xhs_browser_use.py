"""基于Browser-Use的小红书AI爬虫"""
from typing import List
from pydantic import BaseModel, Field
from app.scrapers.browser_use_scraper import BrowserUseScraper
from app.models.attraction import XHSNote
from app.utils.logger import setup_logger
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


class XHSBrowserUseScraper(BrowserUseScraper):
    """基于Browser-Use的小红书AI爬虫"""

    async def search_attraction(self, attraction_name: str, max_notes: int = 5) -> List[XHSNote]:
        """
        使用AI搜索景点相关笔记

        Args:
            attraction_name: 景点名称
            max_notes: 最大笔记数量

        Returns:
            小红书笔记列表
        """
        logger.info(f"开始AI搜索小红书: {attraction_name}")

        # 构建AI任务描述
        task = f"""
任务：在小红书搜索"{attraction_name}"相关的旅游笔记

具体步骤：
1. 访问小红书网站 https://www.xiaohongshu.com
2. 在搜索框搜索关键词："{attraction_name}"
3. 浏览搜索结果，找到前{max_notes}篇相关笔记
4. 对于每篇笔记，提取以下信息：
   - 笔记标题
   - 作者名称
   - 笔记正文内容（尽可能完整）
   - 点赞数、收藏数、评论数
   - 笔记中的图片URL（前3张）
   - 提取笔记中提到的URL链接（特别是官网、预订、门票相关链接）
   - 识别关键词（如：官网、官方网站、预订、门票、开放时间等）

重要提示：
- 优先选择点赞数和收藏数较高的笔记
- 注意提取笔记中提到的实用信息链接
- 如果遇到登录要求，尝试浏览可见内容
- 返回结构化的JSON数据
"""

        # 使用AI执行爬取
        result = await self.scrape_with_task(
            task=task,
            output_model=XHSNotesCollection,
            max_steps=30  # 小红书需要多步操作
        )

        if result["status"] != "success":
            logger.error(f"AI爬取小红书失败: {result.get('error', 'Unknown error')}")
            return []

        # 转换为XHSNote对象
        notes_data = result["data"]
        xhs_notes = []

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

        logger.info(f"成功爬取 {len(xhs_notes)} 篇小红书笔记")
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
