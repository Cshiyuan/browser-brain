"""基于Browser-Use的小红书AI爬虫"""
import asyncio
from typing import List
from datetime import datetime

from app.scrapers.browser_use_scraper import BrowserUseScraper
from app.scrapers.models import XHSNotesCollection, DestinationGuide
from app.models.attraction import XHSNote
from app.models.prompts import XHSPrompts
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class XHSScraper(BrowserUseScraper):
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
        logger.info(f"========== 开始小红书爬取 ==========")
        logger.info(f"目标景点: {attraction_name}, 目标笔记数: {max_notes}")
        logger.info(f"📍 STEP 1: 准备小红书搜索任务 | attraction={attraction_name}, max_notes={max_notes}")

        # 使用提示词模型生成任务
        task = XHSPrompts.search_attraction_task(attraction_name, max_notes)

        # 简单重试逻辑：最多尝试2次
        max_retries = 2
        for attempt in range(max_retries):
            logger.info(f"📍 STEP 2: 调用Browser-Use AI执行小红书爬取（尝试 {attempt + 1}/{max_retries}）")
            result = await self.scrape_with_task(
                task=task,
                output_model=XHSNotesCollection,
                max_steps=30
            )

            # 检查是否成功
            if result["status"] == "success" and result.get("is_successful"):
                break

            # 检测登录/验证码（简化版）
            visited_urls = result.get("urls", [])
            needs_login = any("login" in url.lower() for url in visited_urls)
            needs_captcha = any("captcha" in url.lower() for url in visited_urls)

            if needs_login or needs_captcha:
                wait_msg = "🔐 检测到登录要求" if needs_login else "⚠️  检测到验证码"
                logger.warning(f"{wait_msg}，请在浏览器中完成操作")
                logger.info("⏳ 等待120秒后自动重试...")
                await asyncio.sleep(120)
            elif attempt < max_retries - 1:
                logger.warning("⏳ 等待5秒后重试...")
                await asyncio.sleep(5)

        logger.info(f"📍 STEP 3: 处理AI返回结果 | status={result['status']}")

        if result["status"] != "success" or not result.get("is_successful"):
            logger.error(f"❌ AI爬取小红书失败: {result.get('error', 'Unknown error')}")
            logger.error(f"执行步骤数: {result.get('steps', 0)}, 访问的URL: {result.get('urls', [])}")
            return []

        # 转换为XHSNote对象
        notes_data = result["data"]
        xhs_notes = []

        # 处理 AI Agent 失败返回字符串的情况
        if isinstance(notes_data, str):
            logger.warning(f"⚠️  AI返回数据格式异常: {type(notes_data)}")
            logger.debug(f"原始返回数据: {notes_data}")
            return []

        logger.info(f"AI成功返回 {len(notes_data.notes)} 篇笔记数据")
        logger.info(f"📍 STEP 4: 转换笔记数据为XHSNote对象 | note_count={len(notes_data.notes)}")

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
                created_at=datetime.now().isoformat()  # 转换为ISO格式字符串
            )
            xhs_notes.append(note)
            logger.debug(f"笔记 {idx + 1}: {note.title[:30]}... (点赞:{note.likes}, 收藏:{note.collects})")

        logger.info(f"✅ 成功爬取 {len(xhs_notes)} 篇小红书笔记")
        logger.info(f"========== 小红书爬取完成 ==========")
        return xhs_notes

    async def search_destination_guide(self, destination: str, max_attractions: int = 5) -> List[str]:
        """
        搜索目的地旅游攻略，提取推荐景点列表

        Args:
            destination: 目的地城市/地区
            max_attractions: 最多提取景点数量

        Returns:
            推荐景点名称列表
        """
        logger.info(f"========== 开始搜索目的地攻略 ==========")
        logger.info(f"目的地: {destination}, 目标景点数: {max_attractions}")
        logger.info(f"📍 STEP 1: 准备目的地攻略搜索任务 | destination={destination}")

        # 使用提示词模型生成任务
        task = XHSPrompts.search_destination_guide_task(destination, max_attractions)

        # 简单重试逻辑
        max_retries = 2
        for attempt in range(max_retries):
            logger.info(f"📍 STEP 2: 调用Browser-Use AI执行目的地攻略爬取（尝试 {attempt + 1}/{max_retries}）")
            result = await self.scrape_with_task(
                task=task,
                output_model=DestinationGuide,
                max_steps=30
            )

            if result["status"] == "success" and result.get("is_successful"):
                break

            if attempt < max_retries - 1:
                logger.warning("⏳ 等待5秒后重试...")
                await asyncio.sleep(5)

        logger.info(f"📍 STEP 3: 处理AI返回结果 | status={result['status']}")

        if result["status"] != "success" or not result.get("is_successful"):
            logger.error(f"❌ AI爬取目的地攻略失败: {result.get('error', 'Unknown error')}")
            return []

        guide_data = result["data"]
        if not guide_data:
            logger.error("❌ AI未返回任何数据")
            return []

        logger.info(f"AI成功返回 {len(guide_data.recommended_attractions)} 个推荐景点")
        logger.info(f"📍 STEP 4: 提取景点名称列表 | attraction_count={len(guide_data.recommended_attractions)}")

        # 按优先级排序
        sorted_attractions = sorted(
            guide_data.recommended_attractions,
            key=lambda x: x.priority,
            reverse=True
        )

        # 提取景点名称
        attraction_names = []
        for attr in sorted_attractions[:max_attractions]:
            attraction_names.append(attr.name)
            logger.info(f"  📍 {attr.name} (优先级: {attr.priority}) - {attr.reason[:50]}...")

        logger.info(f"✅ 成功提取 {len(attraction_names)} 个推荐景点")
        logger.info(f"========== 目的地攻略搜索完成 ==========")
        return attraction_names

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
