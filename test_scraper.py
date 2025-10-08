"""测试Browser-Use爬虫 - 有头浏览器模式"""
import asyncio
from app.scrapers.xhs_scraper import XHSScraper
from app.scrapers.official_scraper import OfficialScraper
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


async def test_xhs_scraper():
    """测试小红书爬虫 - 显示浏览器窗口"""
    print("=" * 60)
    print("🚀 开始测试小红书爬虫 (有头浏览器模式)")
    print("=" * 60)

    scraper = XHSScraper(headless=False)  # 显示浏览器窗口!

    try:
        print("\n📌 正在搜索: 故宫")
        print("💡 你应该能看到Chrome窗口打开并自动操作...\n")

        notes = await scraper.search_attraction("故宫", max_notes=3)

        print(f"\n✅ 爬取完成! 获得 {len(notes)} 篇笔记")

        if notes:
            for i, note in enumerate(notes, 1):
                print(f"\n📝 笔记 {i}:")
                print(f"  标题: {note.title}")
                print(f"  作者: {note.author}")
                print(f"  点赞: {note.likes}, 收藏: {note.collects}")
                print(f"  内容预览: {note.content[:100]}...")
        else:
            print("⚠️  未获取到笔记数据")

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await scraper.close()
        print("\n🔒 浏览器已关闭")


async def test_official_scraper():
    """测试官网爬虫 - 显示浏览器窗口"""
    print("\n" + "=" * 60)
    print("🚀 开始测试官网爬虫 (有头浏览器模式)")
    print("=" * 60)

    scraper = OfficialScraper(headless=False)  # 显示浏览器窗口!

    try:
        print("\n📌 正在搜索: 故宫官网")
        print("💡 你应该能看到Chrome窗口打开并自动操作...\n")

        info = await scraper.get_official_info("故宫")

        if info:
            print(f"\n✅ 爬取完成!")
            print(f"  官网: {info.website}")
            print(f"  开放时间: {info.opening_hours}")
            print(f"  门票价格: {info.ticket_price}")
            print(f"  地址: {info.address}")
        else:
            print("⚠️  未获取到官网信息")

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await scraper.close()
        print("\n🔒 浏览器已关闭")


async def main():
    print("\n🎯 Browser-Use 爬虫测试")
    print("=" * 60)
    print("配置:")
    print("  - headless=False (显示浏览器)")
    print("  - wait_between_actions=1.0 (模拟人类速度)")
    print("  - use_vision=True (AI视觉能力)")
    print("=" * 60)

    # 测试小红书爬虫
    await test_xhs_scraper()

    # 等待一下,避免API配额问题
    print("\n⏳ 等待60秒,避免API配额限制...")
    await asyncio.sleep(60)

    # 测试官网爬虫
    await test_official_scraper()

    print("\n" + "=" * 60)
    print("🎉 所有测试完成!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
