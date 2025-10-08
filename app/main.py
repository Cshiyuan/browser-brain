"""
AI Travel Planner - 基于Browser-Use AI驱动的智能旅行规划系统
"""
import asyncio
from app.agents.planner_agent import PlannerAgent
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


async def main():
    """主程序入口"""
    print("=" * 70)
    print("🤖 AI智能旅行规划助手 (Powered by Browser-Use)")
    print("=" * 70)

    # 获取用户输入
    departure = input("\n📍 出发地: ").strip()
    destination = input("📍 目的地: ").strip()
    days = input("📅 游玩天数: ").strip()
    must_visit = input("🎯 必去景点（用逗号分隔）: ").strip()

    # 解析必去景点
    must_visit_list = [spot.strip() for spot in must_visit.split(",") if spot.strip()]

    logger.info(f"开始AI规划行程: {departure} -> {destination}, {days}天")
    logger.info(f"必去景点: {must_visit_list}")

    # 创建AI规划Agent
    planner = PlannerAgent()

    try:
        print("\n🤖 AI Agent正在智能规划中...")
        print("   - AI正在搜索小红书...")
        print("   - AI正在访问官方网站...")
        print("   - AI正在生成最佳方案...")
        print()

        # 执行AI旅行规划
        result = await planner.plan_trip(
            departure=departure,
            destination=destination,
            days=int(days),
            must_visit=must_visit_list
        )

        # 输出结果
        print("\n" + "=" * 70)
        print("✨ AI旅行方案已生成")
        print("=" * 70)
        print(result)

    except Exception as e:
        logger.error(f"AI规划失败: {e}", exc_info=True)
        print(f"\n❌ AI规划失败: {e}")
        print("💡 提示: 请检查API Key配置和网络连接")


if __name__ == "__main__":
    asyncio.run(main())
