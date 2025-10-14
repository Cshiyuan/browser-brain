"""基于Browser-Use的官网AI爬虫"""
from typing import List, Optional

from app.scrapers.browser_use_scraper import BrowserUseScraper
from app.scrapers.models import OfficialInfoOutput, XHSAttractionInformation
from app.models.attraction import OfficialInfo
from app.models.prompts import OfficialPrompts
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class OfficialScraper(BrowserUseScraper):
    """基于Browser-Use的官网AI爬虫"""

    async def get_official_info(
        self,
        attraction_name: str,
        xhs_information: List[XHSAttractionInformation]
    ) -> Optional[OfficialInfo]:
        """
        使用AI获取景点官方信息

        策略：
        1. 使用搜索引擎查找官网
        2. AI自动访问官网并提取信息

        Args:
            attraction_name: 景点名称
            xhs_information: 小红书知识点列表（暂时未使用）

        Returns:
            官方信息对象
        """
        logger.info(f"========== 开始官网信息爬取 ==========")
        logger.info(f"目标景点: {attraction_name}, 参考知识点数: {len(xhs_information)}")
        logger.info(f"📍 STEP 1: 准备官网信息爬取任务 | attraction={attraction_name}")

        # 注意：新设计中不再依赖小红书链接，直接搜索官网
        collected_links: List[str] = []
        logger.info(f"知识点模型中不提供链接，直接搜索官网")

        # 使用提示词模型生成任务
        if collected_links:
            task = OfficialPrompts.get_official_info_with_links_task(attraction_name, collected_links)
        else:
            task = OfficialPrompts.get_official_info_without_links_task(attraction_name)

        # 使用AI执行爬取
        logger.info("📍 STEP 2: 调用Browser-Use AI执行官网信息爬取")
        result = await self.scrape(
            task=task,
            output_model=OfficialInfoOutput,
            max_steps=25
        )

        logger.info(f"📍 STEP 3: 处理AI返回结果 | status={result['status']}")

        if result["status"] != "success":
            logger.warning(f"⚠️  AI获取官网信息失败: {result.get('error', 'Unknown error')}")
            logger.warning(f"执行步骤数: {result.get('steps', 0)}, 访问的URL: {result.get('urls', [])}")
            return None

        # 转换为OfficialInfo对象
        data = result["data"]

        # 处理 AI Agent 失败返回 None 或字符串的情况
        if data is None or isinstance(data, str):
            logger.warning(f"⚠️  AI返回数据格式异常或无数据: {type(data)}")
            logger.debug(f"原始返回数据: {data}")
            return None

        logger.info(f"AI成功返回官网信息数据")
        logger.info("📍 STEP 4: 转换数据为OfficialInfo对象")

        official_info = OfficialInfo(
            name=attraction_name,
            website=data.website or "",
            opening_hours=data.opening_hours or "",
            ticket_price=data.ticket_price or "",
            booking_info=data.booking_method or "",
            address=data.address or "",
            phone=data.phone or "",
            description=data.description or ""
        )

        logger.info(f"✅ 成功获取官网信息: {attraction_name}")
        logger.debug(f"官网: {official_info.website}")
        logger.debug(f"地址: {official_info.address}")
        logger.debug(f"门票: {official_info.ticket_price}")
        logger.info(f"========== 官网信息爬取完成 ==========")
        return official_info
