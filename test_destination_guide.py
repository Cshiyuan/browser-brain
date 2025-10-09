"""测试目的地攻略搜索功能"""
import asyncio
from app.scrapers.xhs_scraper import XHSScraper


async def test_search_destination_guide():
    """测试搜索目的地攻略并提取推荐景点"""
    print("=" * 60)
    print("测试：搜索目的地攻略并提取推荐景点")
    print("=" * 60)

    # 创建爬虫实例（显示浏览器，方便观察）
    scraper = XHSScraper(headless=False)

    try:
        # 测试搜索北京的旅游攻略
        destination = "北京"
        print(f"\n正在搜索 {destination} 的旅游攻略...")

        recommended_attractions = await scraper.search_destination_guide(
            destination=destination,
            max_attractions=5
        )

        print("\n" + "=" * 60)
        print("测试结果")
        print("=" * 60)
        print(f"\n提取到 {len(recommended_attractions)} 个推荐景点:")
        for idx, attraction in enumerate(recommended_attractions, 1):
            print(f"  {idx}. {attraction}")

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

    finally:
        await scraper.close()


if __name__ == "__main__":
    asyncio.run(test_search_destination_guide())
