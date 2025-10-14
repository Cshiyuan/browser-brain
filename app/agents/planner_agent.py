"""旅行规划Agent - 基于Browser-Use AI"""
import asyncio
from typing import List, Any, Coroutine, Union, Dict
from datetime import datetime, timedelta

from app.scrapers import DestinationGuide
from app.scrapers.xhs_scraper import XHSScraper
from app.scrapers.official_scraper import OfficialScraper
from app.models.attraction import Attraction
from app.models.trip_plan import TripPlan, DailyItinerary
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

        注意:
            不再需要传递 log_callback，使用全局 log_manager 管理日志
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

    def _log(self, message: str):
        """内部日志方法"""
        logger.info(message)

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
        self._log("=" * 60)
        self._log(f"🚀 开始AI驱动旅行规划")
        self._log(f"   出发地: {departure}")
        self._log(f"   目的地: {destination}")
        self._log(f"   天数: {days}天")
        self._log(f"   必去景点: {must_visit if must_visit else '无（自动规划）'}")
        self._log("=" * 60)

        try:
            # 步骤1: 使用AI收集景点信息
            self._log("📍 [步骤1/3] 开始收集景点信息...")

            # 补充爬取景点
            if not must_visit:
                guide_data = await self._collect_destination(destination)
                for visit in guide_data.recommended_attractions:
                    must_visit.append(visit.name)

            # 根据景点，并发拉取数据
            await self._collect_attractions(destination, must_visit)
            self._log(f"✅ [步骤1/3] 完成，收集到 {len(self.attractions)} 个景点")

            # 步骤2: 生成行程方案
            self._log("📅 [步骤2/3] 开始生成行程方案...")
            trip_plan = await self._generate_trip_plan(
                departure=departure,
                destination=destination,
                days=days
            )
            self._log("✅ [步骤2/3] 行程方案生成完成")

            # 步骤3: 格式化输出
            self._log("📝 [步骤3/3] 开始格式化输出...")
            result = self._format_plan(trip_plan)
            self._log("✅ [步骤3/3] 格式化完成")
            self._log("🎉 旅行规划全部完成！")
            self._log("=" * 60)
            return result

        except Exception as e:
            logger.error("=" * 60)
            logger.error(f"❌ AI规划失败: {e}", exc_info=True)
            logger.error("=" * 60)
            raise
        finally:
            # 确保清理所有 scraper 资源
            await self._cleanup_all_scrapers()

    async def _collect_destination(self, destination: str) -> DestinationGuide | None:
        self._log(f"   🔍 搜索 {destination} 的旅游攻略...")
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
            self._log("   ⚠️  未能从攻略中提取到推荐景点，将自动收集景点方案")
            return None

        self._log(
            f"   ✅ 成功从攻略中提取 {len(guide_data.recommended_attractions)} 个推荐景点: {guide_data.recommended_attractions}")
        # 使用提取的景点作为必去景点
        return guide_data

    async def _collect_attractions(self, destination: str, must_visit: List[str]):
        """使用批量方法并发收集景点信息"""

        # 步骤1: 批量爬取小红书数据
        self._log(f"   📱 步骤1: 批量爬取小红书数据...")
        xhs_scraper = XHSScraper(headless=self.headless)
        # 注册到活跃列表
        self.active_scrapers.append(xhs_scraper)

        xhs_results = await xhs_scraper.search_attractions_batch(
            attractions=must_visit,
            max_notes=settings.XHS_MAX_NOTES,
            max_concurrent=3  # 最多3个并发
        )

        self._log(f"   ✅ 小红书数据收集完成: {len(xhs_results)} 个景点")

        # 步骤2: 逐个爬取官网数据（保持现有逻辑）
        self._log(f"   🌐 步骤2: 爬取官网数据...")
        success_count = 0
        fail_count = 0

        for idx, attraction_name in enumerate(must_visit, 1):
            try:
                self._log(f"   📍 [{idx}/{len(must_visit)}] 爬取官网: {attraction_name}")

                # 获取小红书知识点
                xhs_information = xhs_results.get(attraction_name, [])

                # 爬取官网信息
                official_scraper = OfficialScraper(headless=self.headless)
                # 注册到活跃列表
                self.active_scrapers.append(official_scraper)
                official_info = await official_scraper.get_official_info(attraction_name, xhs_information)

                # 构建景点对象
                attraction = Attraction(name=attraction_name, city=destination)

                # 添加小红书知识点数据
                attraction.add_raw_data("xiaohongshu", {
                    "information": [info.dict() for info in xhs_information],
                    "total_count": len(xhs_information)
                })

                # 添加官网信息
                if official_info:
                    attraction.add_raw_data("official",
                                            official_info.dict() if hasattr(official_info, 'dict') else official_info)

                # 计算推荐分数
                attraction.recommendation_score = self._calculate_recommendation_score(attraction)

                self.attractions.append(attraction)
                success_count += 1
                self._log(
                    f"   ✅ [{idx}/{len(must_visit)}] 成功: {attraction_name} (评分: {attraction.recommendation_score:.1f})")

            except Exception as e:
                fail_count += 1
                self._log(f"   ❌ [{idx}/{len(must_visit)}] 失败: {attraction_name} - {e}")

        self._log(f"   📊 收集统计: 成功 {success_count} 个, 失败 {fail_count} 个")

    def _calculate_recommendation_score(self, attraction: Attraction) -> float:
        """计算景点推荐分数"""
        score = 0.0

        # 小红书热度（基于知识点热度分数）
        xhs_data = attraction.get_context("raw_data.xiaohongshu")
        if xhs_data and "information" in xhs_data:
            information = xhs_data["information"]
            if information:
                avg_popularity = sum(
                    info.get("popularity_score", 0)
                    for info in information
                ) / len(information)
                score += min(avg_popularity / 100, 50)

        # 有官网信息加分
        if attraction.get_context("raw_data.official"):
            score += 20

        # 基础分数
        score += 30

        return min(score, 100)

    async def _generate_trip_plan(
            self,
            departure: str,
            destination: str,
            days: int
    ) -> TripPlan:
        """
        生成旅行方案

        Args:
            departure: 出发地
            destination: 目的地
            days: 天数

        Returns:
            旅行方案
        """
        logger.info(f"   📝 生成{days}天行程方案...")
        logger.info(f"   🏆 按推荐分数排序景点...")

        # 按推荐分数排序景点
        sorted_attractions = sorted(
            self.attractions,
            key=lambda x: x.recommendation_score,
            reverse=True
        )

        # 创建每日行程
        logger.info(f"   📅 规划{days}天行程安排...")
        daily_itineraries = []
        attractions_per_day = max(1, len(sorted_attractions) // days) if sorted_attractions else 0

        start_date = datetime.now().date()

        for day in range(1, days + 1):
            start_idx = (day - 1) * attractions_per_day
            end_idx = start_idx + attractions_per_day

            if day == days:
                end_idx = len(sorted_attractions)

            day_attractions = sorted_attractions[start_idx:end_idx]

            # 生成当天行程描述
            day_notes = self._generate_day_notes(day_attractions)
            attraction_names = [attr.name for attr in day_attractions]

            logger.info(f"      第{day}天: {', '.join(attraction_names) if attraction_names else '自由活动'}")

            daily_itinerary = DailyItinerary(
                day=day,
                date=str(start_date + timedelta(days=day - 1)),
                title=f"第{day}天行程",
                morning=f"游览: {', '.join(attraction_names[:len(attraction_names) // 2]) if attraction_names else '自由活动'}",
                afternoon=f"游览: {', '.join(attraction_names[len(attraction_names) // 2:]) if len(attraction_names) > 1 else '休息'}",
                evening="品尝当地美食",
                meals=["早餐：酒店", "午餐：景区附近", "晚餐：特色美食"],
                accommodation="当地酒店",
                notes="\n".join(day_notes) if day_notes else "注意提前预订门票"
            )

            daily_itineraries.append(daily_itinerary)

        # 创建旅行方案
        trip_plan = TripPlan(
            plan_id=f"plan_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            destination=destination,
            title=f"{destination}{days}日游 (AI生成)"
        )

        # 设置用户偏好
        trip_plan.set_user_preference("days", days)
        trip_plan.set_user_preference("departure", departure)

        # 添加收集的景点数据
        for attr in sorted_attractions:
            trip_plan.add_attraction(attr)

        # 设置 AI 规划内容
        ai_planning = {
            "itinerary": {
                f"day{itinerary.day}": {
                    "day": itinerary.day,
                    "date": itinerary.date,
                    "title": itinerary.title,
                    "morning": itinerary.morning,
                    "afternoon": itinerary.afternoon,
                    "evening": itinerary.evening,
                    "meals": itinerary.meals,
                    "accommodation": itinerary.accommodation,
                    "notes": itinerary.notes
                }
                for itinerary in daily_itineraries
            },
            "highlights": self._extract_highlights(sorted_attractions),
            "tips": self._generate_tips(sorted_attractions),
            "budget": {"estimated_total": len(sorted_attractions) * 100}  # 简单预估
        }
        trip_plan.set_ai_planning(ai_planning)

        return trip_plan

    def _generate_day_notes(self, attractions: List[Attraction]) -> List[str]:
        """生成每日注意事项"""
        notes = []

        for attraction in attractions:
            # 从 context 中获取小红书知识点
            xhs_data = attraction.get_context("raw_data.xiaohongshu", {})
            xhs_information = xhs_data.get("information", [])[:2]

            for info in xhs_information:
                info_data = info.get("attraction_information", {})
                content = extract_text_from_any(info_data)
                if any(keyword in content for keyword in ["提前", "预约", "排队", "注意"]):
                    snippet = content[:100]
                    notes.append(f"{attraction.name}: {snippet}")

            # 从 context 中获取官网信息
            official_data = attraction.get_context("raw_data.official", {})
            if official_data and "booking_info" in official_data:
                notes.append(f"{attraction.name}: {official_data['booking_info']}")

        return notes[:5]

    def _extract_highlights(self, attractions: List[Attraction]) -> List[str]:
        """提取行程亮点"""
        highlights = []

        for attraction in attractions[:3]:
            # 从 context 中获取小红书知识点
            xhs_data = attraction.get_context("raw_data.xiaohongshu", {})
            xhs_information = xhs_data.get("information", [])[:2]

            for info in xhs_information:
                info_data = info.get("attraction_information", {})
                content = extract_text_from_any(info_data)
                if any(word in content for word in ["必打卡", "绝美", "震撼", "推荐"]):
                    highlights.append(f"{attraction.name}: {content[:50]}...")

        return highlights

    def _generate_tips(self, attractions: List[Attraction]) -> List[str]:
        """生成旅行贴士"""
        tips = [
            "✅ 建议提前预订门票",
            "✅ 注意景区开放时间",
            "✅ 携带身份证和学生证（如有）",
            "✅ 关注天气预报，做好防晒/防雨准备",
            "🤖 本方案由AI智能生成，建议出发前再次核实信息"
        ]

        for attraction in attractions:
            # 从 context 中获取小红书知识点
            xhs_data = attraction.get_context("raw_data.xiaohongshu", {})
            xhs_information = xhs_data.get("information", [])

            for info in xhs_information:
                info_data = info.get("attraction_information", {})
                content = extract_text_from_any(info_data)
                if "建议" in content or "攻略" in content:
                    tips.append(f"{attraction.name}攻略详见小红书")
                    break

        return tips

    def _format_plan(self, plan: TripPlan) -> str:
        """格式化输出方案"""
        output = []

        output.append(f"\n{'=' * 60}")
        output.append(f"  {plan.title}")
        output.append(f"  🤖 Powered by Browser-Use AI")
        output.append(f"{'=' * 60}\n")

        # 从 context 中获取行程数据
        itinerary_data = plan.get("ai_planning.itinerary", {})

        for day_key in sorted(itinerary_data.keys()):
            day_info = itinerary_data[day_key]
            output.append(f"\n📅 第{day_info.get('day', '?')}天 ({day_info.get('date', '?')})")
            output.append(f"   {day_info.get('title', '')}")
            output.append("-" * 40)

            if day_info.get('morning'):
                output.append(f"  🌅 上午: {day_info['morning']}")
            if day_info.get('afternoon'):
                output.append(f"  ☀️  下午: {day_info['afternoon']}")
            if day_info.get('evening'):
                output.append(f"  🌙 晚上: {day_info['evening']}")

            if day_info.get('meals'):
                output.append(f"\n  🍽️  餐饮: {', '.join(day_info['meals'])}")

            if day_info.get('accommodation'):
                output.append(f"  🏨 住宿: {day_info['accommodation']}")

            if day_info.get('notes'):
                output.append(f"\n  💡 提示: {day_info['notes'][:100]}")

        # 预算信息
        budget = plan.get("ai_planning.budget", {})
        if budget:
            output.append(f"\n\n💰 预算估算")
            output.append("-" * 40)
            output.append(f"  预估总计: ¥{budget.get('estimated_total', 0):.0f}")

        # 行程亮点
        highlights = plan.get("ai_planning.highlights", [])
        if highlights:
            output.append(f"\n\n✨ 行程亮点")
            output.append("-" * 40)
            for highlight in highlights:
                output.append(f"  • {highlight}")

        # 旅行贴士
        tips = plan.get("ai_planning.tips", [])
        if tips:
            output.append(f"\n\n💡 旅行贴士")
            output.append("-" * 40)
            for tip in tips:
                output.append(f"  • {tip}")

        output.append(f"\n{'=' * 60}\n")

        return "\n".join(output)
