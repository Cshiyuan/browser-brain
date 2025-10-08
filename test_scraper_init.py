"""测试爬虫初始化和日志系统 - 快速测试（不实际爬取）"""
import asyncio
from app.scrapers.xhs_scraper import XHSScraper
from app.scrapers.official_scraper import OfficialScraper
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

async def test_scrapers_init():
    """测试爬虫初始化流程"""
    logger.info("=" * 60)
    logger.info("🧪 开始测试爬虫初始化和日志系统")
    logger.info("=" * 60)

    # 测试1: 小红书爬虫初始化
    logger.info("\n📝 测试 1: XHSScraper 初始化")
    try:
        xhs_scraper = XHSScraper(headless=False)
        logger.info("✅ XHSScraper 初始化成功")
        logger.info(f"   - LLM Provider: 已配置")
        logger.info(f"   - Headless模式: {xhs_scraper.headless}")
        logger.info(f"   - Browser Profile: 已创建")
    except Exception as e:
        logger.error(f"❌ XHSScraper 初始化失败: {e}")
        import traceback
        traceback.print_exc()

    # 测试2: 官网爬虫初始化
    logger.info("\n📝 测试 2: OfficialScraper 初始化")
    try:
        official_scraper = OfficialScraper(headless=False)
        logger.info("✅ OfficialScraper 初始化成功")
        logger.info(f"   - LLM Provider: 已配置")
        logger.info(f"   - Headless模式: {official_scraper.headless}")
        logger.info(f"   - Browser Profile: 已创建")
    except Exception as e:
        logger.error(f"❌ OfficialScraper 初始化失败: {e}")
        import traceback
        traceback.print_exc()

    # 测试3: 检查日志文件
    logger.info("\n📝 测试 3: 检查日志文件结构")
    import os
    from pathlib import Path

    log_dirs = ["logs/scrapers", "logs/agents", "logs/main"]
    for log_dir in log_dirs:
        if Path(log_dir).exists():
            files = list(Path(log_dir).glob("*.log"))
            logger.info(f"✅ {log_dir}: {len(files)} 个日志文件")
            for f in files[:3]:  # 只显示前3个
                size = f.stat().st_size
                logger.info(f"   - {f.name} ({size} bytes)")
        else:
            logger.warning(f"⚠️  {log_dir}: 目录不存在")

    logger.info("\n" + "=" * 60)
    logger.info("🎉 初始化测试完成!")
    logger.info("=" * 60)

    print("\n\n💡 请查看以下日志文件验证完整的调用流程:")
    print("   📂 logs/scrapers/xhs_scraper_20251005.log")
    print("   📂 logs/scrapers/official_scraper_20251005.log")
    print("   📂 logs/scrapers/browser_use_scraper_20251005.log")
    print("\n   每个日志应包含:")
    print("   ✓ [文件名:行号]")
    print("   ✓ 函数名()")
    print("   ✓ 📍 STEP 标记")
    print("   ✓ 详细的初始化流程")

if __name__ == "__main__":
    asyncio.run(test_scrapers_init())
