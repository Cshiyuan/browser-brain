"""旅行规划Agent - 基于Browser-Use AI"""
import asyncio
from typing import List
from datetime import datetime, timedelta
from app.scrapers.xhs_scraper import XHSScraper
from app.scrapers.official_scraper import OfficialScraper
from app.models.attraction import Attraction
from app.models.trip_plan import TripPlan, DailyItinerary
from app.utils.logger import setup_logger
from config.settings import settings

logger = setup_logger(__name__)


class PlannerAgent:
    """基于Browser-Use的AI旅行规划Agent"""

    def __init__(self, headless: bool = None, log_callback=None):
        """
        初始化规划Agent

        Args:
            headless: 是否无头模式（None则使用配置文件）
            log_callback: 日志回调函数，用于将日志传递到前端
        """
        self.headless = headless if headless is not None else settings.HEADLESS
        self.attractions: List[Attraction] = []
        self.log_callback = log_callback

    def _log(self, message: str):
        """内部日志方法：同时输出到logger和前端"""
        logger.info(message)
        if self.log_callback:
            self.log_callback(message)

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
        self._log("="*60)
        self._log(f"🚀 开始AI驱动旅行规划")
        self._log(f"   出发地: {departure}")
        self._log(f"   目的地: {destination}")
        self._log(f"   天数: {days}天")
        self._log(f"   必去景点: {must_visit if must_visit else '无（自由行）'}")
        self._log("="*60)

        try:
            # 步骤1: 使用AI收集景点信息
            self._log("📍 [步骤1/3] 开始收集景点信息...")
            await self._collect_attractions_with_ai(destination, must_visit)
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
            self._log("="*60)
            return result

        except Exception as e:
            logger.error("="*60)
            logger.error(f"❌ AI规划失败: {e}", exc_info=True)
            logger.error("="*60)
            raise

    async def _collect_attractions_with_ai(self, destination: str, must_visit: List[str]):
        """
        使用AI收集景点信息（Browser-Use）

        Args:
            destination: 目的地
            must_visit: 必去景点
        """
        if not must_visit:
            self._log("   ℹ️  未指定必去景点，将生成自由行方案")
            return

        self._log(f"   🎯 目标景点: {must_visit}")
        self._log(f"   🤖 启动AI爬虫...")

        # 创建AI爬虫实例（共享浏览器）
        xhs_scraper = XHSScraper(headless=self.headless)
        official_scraper = OfficialScraper(headless=self.headless)

        try:
            # 为每个景点创建AI爬取任务
            tasks = []
            for idx, attraction_name in enumerate(must_visit, 1):
                self._log(f"   📌 [{idx}/{len(must_visit)}] 准备爬取: {attraction_name}")
                task = self._scrape_single_attraction_ai(
                    destination,
                    attraction_name,
                    xhs_scraper,
                    official_scraper
                )
                tasks.append(task)

            # 并发执行AI爬取
            self._log(f"   ⚡ 并发执行 {len(tasks)} 个爬取任务...")
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # 收集成功的结果
            success_count = 0
            fail_count = 0
            for idx, result in enumerate(results, 1):
                if isinstance(result, Attraction):
                    self.attractions.append(result)
                    success_count += 1
                    self._log(f"   ✅ [{idx}/{len(results)}] 成功收集: {result.name} (评分: {result.recommendation_score:.1f})")
                else:
                    fail_count += 1
                    self._log(f"   ❌ [{idx}/{len(results)}] 失败: {result}")

            self._log(f"   📊 收集统计: 成功 {success_count} 个, 失败 {fail_count} 个")

        finally:
            # 关闭爬虫（释放浏览器）
            self._log("   🔒 关闭AI爬虫...")
            await xhs_scraper.close()
            await official_scraper.close()

    async def _scrape_single_attraction_ai(
        self,
        city: str,
        attraction_name: str,
        xhs_scraper: XHSScraper,
        official_scraper: OfficialScraper
    ) -> Attraction:
        """
        使用AI爬取单个景点的信息

        Args:
            city: 城市
            attraction_name: 景点名称
            xhs_scraper: 小红书AI爬虫
            official_scraper: 官网AI爬虫

        Returns:
            景点对象
        """
        logger.info(f"AI开始爬取景点: {attraction_name}")

        try:
            # AI爬取小红书笔记
            xhs_notes = await xhs_scraper.scrape(
                attraction_name,
                max_notes=settings.XHS_MAX_NOTES
            )

            # AI爬取官网信息
            official_info = await official_scraper.scrape(attraction_name, xhs_notes)

            # 构建景点对象
            attraction = Attraction(
                name=attraction_name,
                city=city
            )

            # 添加小红书数据
            attraction.add_raw_data("xiaohongshu", {
                "notes": [note.dict() for note in xhs_notes],
                "total_notes": len(xhs_notes)
            })

            # 添加官网信息
            if official_info:
                attraction.add_raw_data("official", official_info.dict() if hasattr(official_info, 'dict') else official_info)

            # 计算推荐分数
            attraction.recommendation_score = self._calculate_recommendation_score(attraction)

            logger.info(f"AI成功爬取景点: {attraction_name}, 推荐分数: {attraction.recommendation_score:.1f}")
            return attraction

        except Exception as e:
            logger.error(f"AI爬取景点失败 {attraction_name}: {e}", exc_info=True)
            raise

    def _calculate_recommendation_score(self, attraction: Attraction) -> float:
        """计算景点推荐分数"""
        score = 0.0

        # 小红书热度
        xhs_data = attraction.get_context("raw_data.xiaohongshu")
        if xhs_data and "notes" in xhs_data:
            notes = xhs_data["notes"]
            if notes:
                avg_engagement = sum(
                    note.get("likes", 0) + note.get("collects", 0)
                    for note in notes
                ) / len(notes)
                score += min(avg_engagement / 1000, 50)

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
                morning=f"游览: {', '.join(attraction_names[:len(attraction_names)//2]) if attraction_names else '自由活动'}",
                afternoon=f"游览: {', '.join(attraction_names[len(attraction_names)//2:]) if len(attraction_names) > 1 else '休息'}",
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
            # 从 context 中获取小红书笔记
            xhs_data = attraction.get_context("raw_data.xiaohongshu", {})
            xhs_notes = xhs_data.get("notes", [])[:2]

            for note in xhs_notes:
                content = note.get("content", "")
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
            # 从 context 中获取小红书笔记
            xhs_data = attraction.get_context("raw_data.xiaohongshu", {})
            xhs_notes = xhs_data.get("notes", [])[:2]

            for note in xhs_notes:
                content = note.get("content", "")
                title = note.get("title", "")
                if any(word in content for word in ["必打卡", "绝美", "震撼", "推荐"]):
                    highlights.append(f"{attraction.name}: {title}")

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
            # 从 context 中获取小红书笔记
            xhs_data = attraction.get_context("raw_data.xiaohongshu", {})
            xhs_notes = xhs_data.get("notes", [])

            for note in xhs_notes:
                content = note.get("content", "")
                if "建议" in content or "攻略" in content:
                    tips.append(f"{attraction.name}攻略详见小红书")
                    break

        return tips

    def _format_plan(self, plan: TripPlan) -> str:
        """格式化输出方案"""
        output = []

        output.append(f"\n{'='*60}")
        output.append(f"  {plan.title}")
        output.append(f"  🤖 Powered by Browser-Use AI")
        output.append(f"{'='*60}\n")

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

        output.append(f"\n{'='*60}\n")

        return "\n".join(output)
