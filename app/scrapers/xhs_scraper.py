"""基于Browser-Use的小红书AI爬虫"""
import asyncio
from typing import List
from datetime import datetime

from app.scrapers.browser_use_scraper import BrowserUseScraper
from app.scrapers.models import XHSNotesCollection, DestinationGuide
from app.models.attraction import XHSNote
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class XHSScraper(BrowserUseScraper):
    """基于Browser-Use的小红书AI爬虫"""

    async def _handle_manual_intervention(
        self,
        message: str,
        wait_seconds: int = 60,
        prompt_interval: int = 10
    ):
        """
        通用人工介入处理：暂停等待用户手动完成操作

        Args:
            message: 提示消息
            wait_seconds: 等待时间（秒），默认60秒
            prompt_interval: 提示间隔（秒），默认10秒
        """
        logger.warning(message)
        logger.info(f"⏳ 系统将在 {wait_seconds} 秒后自动继续...")

        # 定期提示剩余时间
        for remaining in range(wait_seconds, 0, -prompt_interval):
            logger.info(f"⏱️  剩余等待时间: {remaining} 秒")
            await asyncio.sleep(min(prompt_interval, remaining))

        logger.info("✅ 等待结束，继续执行任务...")

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
- 如果遇到登录要求，直接停留在登录页面等待（不要尝试跳过或关闭登录窗口，系统会自动检测并暂停等待人工登录）
- 遇到验证码时，停留在验证码页面（系统会自动检测并暂停等待人工处理）
- 如果遇到任何弹窗或引导，先关闭它们
- 返回结构化的JSON数据
"""

        # 使用AI执行爬取
        logger.info("📍 STEP 2: 调用Browser-Use AI执行小红书爬取")
        result = await self.scrape_with_task(
            task=task,
            output_model=XHSNotesCollection,
            max_steps=30  # 小红书需要多步操作
        )

        # 检测是否遇到验证码或登录要求
        if result["status"] == "success" and result.get("urls"):
            visited_urls = result["urls"]

            # 检查是否访问了验证码页面
            if any("captcha" in url.lower() for url in visited_urls):
                await self._handle_manual_intervention(
                    "⚠️  检测到验证码，请在浏览器窗口中完成验证码验证",
                    wait_seconds=60,
                    prompt_interval=10
                )
                logger.info("🔄 重新尝试执行爬取任务...")
                result = await self.scrape_with_task(
                    task=task,
                    output_model=XHSNotesCollection,
                    max_steps=30
                )

            # 检查是否访问了登录页面
            elif any("login" in url.lower() or "signin" in url.lower() for url in visited_urls):
                await self._handle_manual_intervention(
                    "🔐 检测到登录要求，请在浏览器窗口中完成登录操作",
                    wait_seconds=120,
                    prompt_interval=15
                )
                logger.info("🔄 重新尝试执行爬取任务...")
                result = await self.scrape_with_task(
                    task=task,
                    output_model=XHSNotesCollection,
                    max_steps=30
                )

        logger.info(f"📍 STEP 3: 处理AI返回结果 | status={result['status']}")

        if result["status"] != "success":
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

        # 构建AI任务描述
        task = f"""
任务：在小红书搜索"{destination}旅游攻略"或"{destination}必去景点"，提取推荐景点列表

具体步骤：
1. 访问小红书网站 https://www.xiaohongshu.com/search_result?keyword={destination}旅游攻略 和 https://www.xiaohongshu.com/search_result?keyword={destination}必去景点
2. 等待页面完全加载(3-5秒)
3. 浏览前5-10篇高赞攻略笔记
4. 从这些攻略笔记中提取：
   - 提到的景点名称（如"故宫"、"长城"、"颐和园"等）
   - 推荐理由（为什么推荐这个景点）
   - 优先级（根据笔记中的描述判断，如"必去"=5，"推荐"=4，"可选"=3）
5. 提取最多{max_attractions}个景点

重要提示：
- 优先选择点赞数和收藏数较高的攻略笔记
- 如果遇到登录要求，直接停留在登录页面等待（不要尝试跳过或关闭登录窗口，status返回login）
- 遇到验证码时，停留在验证码页面（不要尝试跳过或关闭登录窗口，status返回captcha）
- 返回结构化的JSON数据
"""

        # 使用AI执行爬取
        logger.info("📍 STEP 2: 调用Browser-Use AI执行目的地攻略爬取")
        result = await self.scrape_with_task(
            task=task,
            output_model=DestinationGuide,
            max_steps=30
        )

        # 步骤3: 处理返回数据（scrape_with_task已自动转换为Pydantic对象）
        guide_data = result["data"]  # ← 已经是 DestinationGuide 对象

        # 检测是否遇到验证码或登录要求（通过status字段）
        if  guide_data.status == "captcha":
            await self._handle_manual_intervention(
                "⚠️  检测到验证码，请在浏览器窗口中完成验证码验证",
                wait_seconds=60,
                prompt_interval=10
            )
            logger.info("🔄 重新尝试执行爬取任务...")
            result = await self.scrape_with_task(
                task=task,
                output_model=DestinationGuide,
                max_steps=30
            )

        # 检查是否访问了登录页面
        if  guide_data.status == "login":
            await self._handle_manual_intervention(
                "🔐 检测到登录要求，请在浏览器窗口中完成登录操作",
                wait_seconds=120,
                prompt_interval=15
            )
            logger.info("🔄 重新尝试执行爬取任务...")
            result = await self.scrape_with_task(
                task=task,
                output_model=DestinationGuide,
                max_steps=30
            )

        logger.info(f"📍 STEP 3: 处理AI返回结果 | status={result['status']}")

        if result["status"] != "success":
            logger.error(f"❌ AI爬取目的地攻略失败: {result.get('error', 'Unknown error')}")
            logger.error(f"执行步骤数: {result.get('steps', 0)}, 访问的URL: {result.get('urls', [])}")
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
