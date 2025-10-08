"""基于Browser-Use的官网AI爬虫"""
from typing import List, Optional
from pydantic import BaseModel, Field
from app.scrapers.browser_use_scraper import BrowserUseScraper
from app.models.attraction import OfficialInfo, XHSNote
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


# 定义官网信息的结构化输出模型
class OfficialInfoOutput(BaseModel):
    """官网信息输出"""
    website: Optional[str] = Field(None, description="官方网站URL")
    opening_hours: Optional[str] = Field(None, description="开放时间")
    ticket_price: Optional[str] = Field(None, description="门票价格")
    booking_method: Optional[str] = Field(None, description="预订方式")
    address: Optional[str] = Field(None, description="地址")
    phone: Optional[str] = Field(None, description="联系电话")
    description: Optional[str] = Field(None, description="景点描述")


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
        2. 如果没有，使用搜索引擎查找
        3. AI自动访问官网并提取信息

        Args:
            attraction_name: 景点名称
            xhs_notes: 小红书笔记列表

        Returns:
            官方信息对象
        """
        logger.info(f"开始AI获取官方信息: {attraction_name}")

        # 从小红书笔记中收集所有链接
        collected_links = []
        for note in xhs_notes:
            collected_links.extend(note.extracted_links)

        # 去重
        collected_links = list(set(collected_links))

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
1. 使用百度或Google搜索"{attraction_name} 官网"
2. 识别真正的官方网站（通常域名包含景点名称或政府域名.gov.cn）
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
- 优先选择.gov.cn或景点官方域名
- 避免打开第三方旅游平台（如携程、美团等）
- 如果找不到独立官网，可以查找景点所属管理机构的网站
- 返回结构化的JSON数据
"""

        # 使用AI执行爬取
        result = await self.scrape_with_task(
            task=task,
            output_model=OfficialInfoOutput,
            max_steps=25
        )

        if result["status"] != "success":
            logger.warning(f"AI获取官网信息失败: {result.get('error', 'Unknown error')}")
            return None

        # 转换为OfficialInfo对象
        data = result["data"]

        official_info = OfficialInfo(
            website=data.website,
            opening_hours=data.opening_hours,
            ticket_price=data.ticket_price,
            booking_method=data.booking_method,
            address=data.address,
            phone=data.phone,
            description=data.description
        )

        logger.info(f"成功获取官网信息: {attraction_name}")
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
