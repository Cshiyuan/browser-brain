"""基于Browser-Use的小红书AI爬虫"""
import asyncio
from typing import List, Dict
from datetime import datetime

from app.scrapers.browser_use_scraper import BrowserUseScraper
from app.scrapers.models import XHSAttractionInformationCollection, XHSAttractionInformation, XHSAttractionRecommendationCollection
from app.models.prompts import XHSPrompts
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class XHSScraper(BrowserUseScraper):
    """基于Browser-Use的小红书AI爬虫"""

    async def search_attraction(self, attraction_name: str, max_notes: int = 5) -> List[XHSAttractionInformation]:
        """
        使用AI搜索景点相关知识点

        Args:
            attraction_name: 景点名称
            max_notes: 最大笔记数量

        Returns:
            景点知识点列表
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
            result = await self.scrape(
                task=task,
                output_model=XHSAttractionInformationCollection,
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

        # 处理返回的知识点数据
        info_data = result["data"]

        # 处理 AI Agent 失败返回字符串的情况
        if isinstance(info_data, str):
            logger.warning(f"⚠️  AI返回数据格式异常: {type(info_data)}")
            logger.debug(f"原始返回数据: {info_data}")
            return []

        logger.info(f"AI成功返回 {len(info_data.information)} 条知识点")
        logger.info(f"📍 STEP 4: 处理景点知识点数据 | info_count={len(info_data.information)}")

        for idx, info in enumerate(info_data.information):
            logger.debug(f"知识点 {idx + 1}: {info.attraction_name} - {info.attraction_information[:50]}... (热度:{info.popularity_score})")

        logger.info(f"✅ 成功爬取 {len(info_data.information)} 条景点知识点")
        logger.info(f"========== 小红书爬取完成 ==========")
        return info_data.information

    async def search_destination_guide(self, destination: str, max_attractions: int = 5) -> XHSAttractionRecommendationCollection:
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
        max_retries = 5
        for attempt in range(max_retries):
            logger.info(f"📍 STEP 2: 调用Browser-Use AI执行目的地攻略爬取（尝试 {attempt + 1}/{max_retries}）")
            result = await self.scrape(
                task=task,
                output_model=XHSAttractionRecommendationCollection,
                max_steps=30
            )

            if result["status"] == "success" and result.get("is_successful"):
                break

            if attempt < max_retries - 1:
                logger.warning("⏳ 等待30秒后重试...")
                await asyncio.sleep(30)

        logger.info(f"📍 STEP 3: 处理AI返回结果 | status={result['status']}")

        if result["status"] != "success" or not result.get("is_successful"):
            logger.error(f"❌ AI爬取目的地攻略失败: {result.get('error', 'Unknown error')}")
            return XHSAttractionRecommendationCollection(recommended_attractions=[], status="error", msg="爬取失败")

        guide_data = result["data"]
        if not guide_data:
            logger.error("❌ AI未返回任何数据")
            return XHSAttractionRecommendationCollection(recommended_attractions=[], status="error", msg="未返回数据")

        logger.info(f"AI成功返回 {len(guide_data.recommended_attractions)} 个推荐景点")
        logger.info(f"📍 STEP 4: 提取景点名称列表 | attraction_count={len(guide_data.recommended_attractions)}")

        # 按优先级排序
        sorted_attractions = sorted(
            guide_data.recommended_attractions,
            key=lambda x: x.priority,
            reverse=True
        )

        # 提取景点名称
        attraction = []
        for attr in sorted_attractions[:max_attractions]:
            attraction.append(attr)

        guide_data.recommended_attractions = attraction
        return guide_data

    async def search_attractions_batch(
        self,
        attractions: List[str],
        max_notes: int = 5,
        max_concurrent: int = 5
    ) -> Dict[str, List[XHSAttractionInformation]]:
        """
        批量并发爬取多个景点的知识点

        Args:
            attractions: 景点名称列表
            max_notes: 每个景点的最大笔记数
            max_concurrent: 最大并发数（默认5）

        Returns:
            字典 {景点名: [知识点列表]}
        """

        def create_task(attraction_name: str) -> str:
            """生成任务提示词"""
            return XHSPrompts.search_attraction_task(attraction_name, max_notes)

        def parse_information(info_data: XHSAttractionInformationCollection) -> List[XHSAttractionInformation]:
            """解析知识点数据"""
            return info_data.information

        # 调用基类的批量爬取方法
        return await self.scrape_batch(
            items=attractions,
            scrape_task_fn=create_task,
            parse_result_fn=parse_information,
            output_model=XHSAttractionInformationCollection,
            max_concurrent=max_concurrent,
            max_steps=30,
            item_label="景点"
        )
