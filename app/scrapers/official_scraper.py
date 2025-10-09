"""基于Browser-Use的官网AI爬虫"""
from typing import List, Optional

from app.scrapers.browser_use_scraper import BrowserUseScraper
from app.scrapers.models import OfficialInfoOutput
from app.models.attraction import OfficialInfo, XHSNote
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class OfficialScraper(BrowserUseScraper):
    """基于Browser-Use的官网AI爬虫"""

    async def get_official_info(
        self,
        attraction_name: str,
        xhs_notes: List[XHSNote]
    ) -> Optional[OfficialInfo]:
        """
        使用AI获取景点官方信息

        策略：
        1. 优先从小红书笔记中提取的链接
        2. 如果没有,使用搜索引擎查找
        3. AI自动访问官网并提取信息

        Args:
            attraction_name: 景点名称
            xhs_notes: 小红书笔记列表

        Returns:
            官方信息对象
        """
        logger.info(f"========== 开始官网信息爬取 ==========")
        logger.info(f"目标景点: {attraction_name}, 参考笔记数: {len(xhs_notes)}")
        logger.info(f"📍 STEP 1: 准备官网信息爬取任务 | attraction={attraction_name}")

        # 从小红书笔记中收集所有链接
        collected_links = []
        for note in xhs_notes:
            # 如果有 url 字段,添加到链接列表
            if note.url:
                collected_links.append(note.url)

        # 去重
        collected_links = list(set(collected_links))
        logger.info(f"从小红书笔记中收集到 {len(collected_links)} 个链接")
        logger.debug(f"收集的链接: {collected_links[:5]}")

        # 构建AI任务
        if collected_links:
            task = f"""
任务：查找并提取"{attraction_name}"的官方信息

已知信息：
小红书用户提供的可能的官方链接：
{chr(10).join(['- ' + link for link in collected_links[:5]])}

具体步骤：
1. 首先验证上述链接，找到真正的官方网站
2. 如果上述链接都不是官网，则使用百度或Google搜索"{attraction_name} 官网"
3. 访问官方网站
4. 提取以下信息：
   - 官方网站URL
   - 开放时间/营业时间
   - 门票价格（成人票、学生票、儿童票等）
   - 预订方式（网上预订、现场购票、公众号预约等）
   - 详细地址
   - 联系电话
   - 景点简介/描述

重要提示：
- 确保访问的是官方网站，而不是旅游平台
- 如果官网信息不全，可以访问景点的微信公众号或官方小程序
- 返回结构化的JSON数据
"""
        else:
            task = f"""
任务：查找并提取"{attraction_name}"的官方信息

具体步骤：
1. 访问百度搜索 https://www.baidu.com
2. 等待页面加载(2-3秒)
3. 在搜索框输入："{attraction_name} 官网"
4. 点击搜索或按回车
5. 等待搜索结果加载
6. 识别官方网站（优先选择.gov.cn或包含景点名称的域名）
7. 点击进入官方网站
8. 等待官网加载完成
9. 提取以下信息：
   - 官方网站URL
   - 开放时间/营业时间
   - 门票价格（成人票、学生票、儿童票等）
   - 预订方式（网上预订、现场购票、公众号预约等）
   - 详细地址
   - 联系电话
   - 景点简介/描述

重要提示：
- 像真实用户一样操作，每步之间留有间隔
- 优先选择.gov.cn或景点官方域名
- 避免打开第三方旅游平台（如携程、美团、去哪儿等）
- 如果遇到弹窗或广告，先关闭它们
- 如果百度不可用，可以尝试使用Bing搜索
- 返回结构化的JSON数据
"""

        # 使用AI执行爬取
        logger.info("📍 STEP 2: 调用Browser-Use AI执行官网信息爬取")
        result = await self.scrape_with_task(
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

    async def scrape(
        self,
        attraction_name: str,
        xhs_notes: List[XHSNote]
    ) -> Optional[OfficialInfo]:
        """
        实现基类的抽象方法

        Args:
            attraction_name: 景点名称
            xhs_notes: 小红书笔记列表

        Returns:
            官方信息
        """
        return await self.get_official_info(attraction_name, xhs_notes)
