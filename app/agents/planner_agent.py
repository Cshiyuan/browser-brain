"""旅行规划Agent - 基于Browser-Use AI"""
from typing import List, Any
import google.generativeai as genai

from app.scrapers import XHSAttractionRecommendationCollection
from app.scrapers.xhs_scraper import XHSScraper
from app.models.attraction import Attraction
from app.models.prompts import PlannerPrompts
from app.utils import setup_logger, extract_text_from_any
from config.settings import settings

logger = setup_logger(__name__)


class PlannerAgent:
    """基于Browser-Use的AI旅行规划Agent"""

    def __init__(self, headless: bool = None):
        """
        初始化规划Agent
        Args:
            headless: 是否无头模式（None则使用配置文件）
        """
        self.headless = headless if headless is not None else settings.HEADLESS
        self.attractions: List[Attraction] = []
        self.active_scrapers: List[Any] = []  # 追踪所有活跃的 scraper 实例

    async def _cleanup_all_scrapers(self):
        """清理所有 scraper 的浏览器会话"""
        if not self.active_scrapers:
            logger.debug("无需清理（没有活跃的 scraper）")
            return

        logger.info(f"🧹 清理 {len(self.active_scrapers)} 个 scraper 的浏览器资源...")
        for i, scraper in enumerate(self.active_scrapers[:], 1):
            try:
                await scraper.close()
                logger.debug(f"   ✓ [{i}/{len(self.active_scrapers)}] Scraper 已清理")
            except Exception as e:
                logger.warning(f"   ⚠️  [{i}/{len(self.active_scrapers)}] 清理警告: {e}")

        self.active_scrapers.clear()
        logger.info("✅ 所有 Scraper 资源清理完成")

    async def plan_trip(
            self,
            departure: str,
            destination: str,
            days: int,
            must_visit: List[str]
    ) -> str:
        """
        规划旅行（使用Browser-Use AI爬虫）

        Args:
            departure: 出发地
            destination: 目的地
            days: 天数
            must_visit: 必去景点列表

        Returns:
            旅行方案文本
        """
        logger.info("=" * 60)
        logger.info(f"🚀 开始AI驱动旅行规划")
        logger.info(f"   出发地: {departure}")
        logger.info(f"   目的地: {destination}")
        logger.info(f"   天数: {days}天")
        logger.info(f"   必去景点: {must_visit if must_visit else '无（自动规划）'}")
        logger.info("=" * 60)

        try:
            # 步骤1: 使用AI收集景点信息
            logger.info("📍 [步骤1/2] 开始收集景点信息...")

            # 补充爬取景点
            if not must_visit:
                guide_data = await self._collect_destination(destination)
                for visit in guide_data.recommended_attractions:
                    must_visit.append(visit.name)

            # 根据景点，并发拉取数据
            await self._collect_attractions(destination, must_visit)
            logger.info(f"✅ [步骤1/2] 完成，收集到 {len(self.attractions)} 个景点")

            # 步骤2: 使用 LLM 生成旅行方案
            logger.info("🤖 [步骤2/2] 使用 LLM 生成旅行方案...")
            result = await self._generate_plan_with_llm(
                departure=departure,
                destination=destination,
                days=days
            )
            logger.info("✅ [步骤2/2] 旅行方案生成完成")
            logger.info("🎉 旅行规划全部完成！")
            logger.info("=" * 60)
            return result

        except Exception as e:
            logger.error("=" * 60)
            logger.error(f"❌ AI规划失败: {e}", exc_info=True)
            logger.error("=" * 60)
            raise
        finally:
            # 确保清理所有 scraper 资源
            await self._cleanup_all_scrapers()

    async def _collect_destination(self, destination: str) -> XHSAttractionRecommendationCollection | None:
        logger.info(f"   🔍 搜索 {destination} 的旅游攻略...")
        # 创建临时爬虫实例用于搜索攻略
        xhs_scraper = XHSScraper(
            headless=self.headless,
            keep_alive=True,
        )
        # 注册到活跃列表
        self.active_scrapers.append(xhs_scraper)

        guide_data = await xhs_scraper.search_destination_guide(
            destination=destination,
            max_attractions=5  # 默认提取5个推荐景点
        )
        if not guide_data.recommended_attractions:
            logger.info("   ⚠️  未能从攻略中提取到推荐景点，将自动收集景点方案")
            return None

        logger.info(
            f"   ✅ 成功从攻略中提取 {len(guide_data.recommended_attractions)} 个推荐景点: {guide_data.recommended_attractions}")
        # 使用提取的景点作为必去景点
        return guide_data

    async def _collect_attractions(self, destination: str, must_visit: List[str]):
        """使用批量方法并发收集景点信息"""

        # 步骤1: 批量爬取小红书数据
        logger.info(f"   📱 步骤1: 批量爬取小红书数据...")
        xhs_scraper = XHSScraper(headless=self.headless)
        # 注册到活跃列表
        self.active_scrapers.append(xhs_scraper)

        xhs_results = await xhs_scraper.search_attractions_batch(
            attractions=must_visit,
            max_notes=settings.XHS_MAX_NOTES,
            max_concurrent=3  # 最多3个并发
        )

        logger.info(f"   ✅ 小红书数据收集完成: {len(xhs_results)} 个景点")

        # 步骤2: 构建景点对象
        logger.info(f"   📦 步骤2: 构建景点数据...")
        success_count = 0
        fail_count = 0

        for idx, attraction_name in enumerate(must_visit, 1):
            try:
                logger.info(f"   📍 [{idx}/{len(must_visit)}] 构建景点: {attraction_name}")

                # 获取小红书知识点
                xhs_information = xhs_results.get(attraction_name, [])

                # 构建景点对象
                attraction = Attraction(name=attraction_name, city=destination)

                # 添加小红书知识点数据
                attraction.add_raw_data("xiaohongshu", {
                    "information": [info.model_dump() for info in xhs_information],
                    "total_count": len(xhs_information)
                })

                self.attractions.append(attraction)
                success_count += 1
                logger.info(f"   ✅ [{idx}/{len(must_visit)}] 成功: {attraction_name}")

            except Exception as e:
                fail_count += 1
                logger.info(f"   ❌ [{idx}/{len(must_visit)}] 失败: {attraction_name} - {e}")

        logger.info(f"   📊 收集统计: 成功 {success_count} 个, 失败 {fail_count} 个")

    async def _generate_plan_with_llm(
            self,
            departure: str,
            destination: str,
            days: int
    ) -> str:
        """
        使用 LLM 直接生成旅行方案

        Args:
            departure: 出发地
            destination: 目的地
            days: 天数

        Returns:
            格式化的旅行方案文本
        """
        logger.info("   🤖 调用 Google Gemini 生成旅行计划...")

        # 准备景点数据摘要
        attractions_summary = self._prepare_attractions_summary()

        # 使用统一的提示词模板
        prompt = PlannerPrompts.generate_trip_plan(
            departure=departure,
            destination=destination,
            days=days,
            attractions_summary=attractions_summary
        )

        # 配置并调用 Google Genai
        genai.configure(api_key=settings.GOOGLE_API_KEY)
        model = genai.GenerativeModel(settings.LLM_MODEL)
        response = model.generate_content(prompt)
        llm_output = response.text

        logger.info("   ✅ Google Gemini 生成完成")

        # 格式化最终输出
        output = [
            f"\n{'=' * 60}",
            f"  {destination}{days}日游 (AI生成)",
            f"  🤖 Powered by Browser-Use AI + Google Gemini",
            f"{'=' * 60}\n",
            llm_output,
            f"\n{'=' * 60}\n"
        ]

        return "\n".join(output)

    def _prepare_attractions_summary(self) -> str:
        """准备景点数据摘要供 LLM 使用"""
        output = []

        for attr in self.attractions:
            output.append(f"\n## {attr.name}")
            output.append("-" * 40)

            # 小红书数据
            xhs_data = attr.get_context("raw_data.xiaohongshu", {})
            xhs_info = xhs_data.get("information", [])
            if xhs_info:
                output.append("**小红书知识点**:")
                for idx, info in enumerate(xhs_info[:5], 1):  # 最多5条
                    info_text = extract_text_from_any(info.get("attraction_information", ""))
                    if info_text:
                        output.append(f"{idx}. {info_text[:200]}")

        return "\n".join(output) if output else "暂无详细数据"
