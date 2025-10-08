#!/usr/bin/env python3
"""
Browser-Use Parallel Agents 示例

演示如何使用并行执行功能同时运行多个独立任务
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.scrapers.browser_use_scraper import BrowserUseScraper
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


async def example_1_basic_parallel():
    """
    示例1: 基础并行任务执行

    场景: 同时在3个网站搜索不同内容
    """
    logger.info("=" * 60)
    logger.info("示例1: 基础并行任务执行")
    logger.info("=" * 60)

    # 定义3个完全独立的任务
    tasks = [
        "访问小红书 https://www.xiaohongshu.com 并搜索'北京故宫'，提取第一个笔记标题",
        "访问小红书 https://www.xiaohongshu.com 并搜索'上海外滩'，提取第一个笔记标题",
        "访问小红书 https://www.xiaohongshu.com 并搜索'成都熊猫基地'，提取第一个笔记标题"
    ]

    # 并行执行（3个浏览器同时运行）
    results = await BrowserUseScraper.run_parallel(
        tasks=tasks,
        max_steps=10,
        headless=False  # 显示浏览器，观察并行执行
    )

    # 打印结果
    for result in results:
        logger.info(f"任务 {result['task_index']}: {result['status']}")
        if result['status'] == 'success':
            logger.info(f"  数据: {result.get('data', 'N/A')}")
        else:
            logger.error(f"  错误: {result.get('error', 'Unknown')}")


async def example_2_multi_attraction_scraping():
    """
    示例2: 并行爬取多个景点信息

    场景: 同时爬取5个不同景点的小红书笔记
    """
    logger.info("=" * 60)
    logger.info("示例2: 并行爬取多个景点")
    logger.info("=" * 60)

    attractions = ["北京故宫", "长城", "颐和园", "天坛", "圆明园"]

    # 为每个景点生成任务
    tasks = [
        f"访问小红书搜索'{attr}'，提取最热门的1条笔记的标题和作者"
        for attr in attractions
    ]

    # 启用Fast Mode加速（并行 + Fast Mode = 超快）
    results = await BrowserUseScraper.run_parallel(
        tasks=tasks,
        max_steps=15,
        headless=True,
        fast_mode=True  # 每个任务都使用Fast Mode
    )

    # 统计结果
    success_count = sum(1 for r in results if r['status'] == 'success')
    logger.info(f"✅ 成功爬取 {success_count}/{len(attractions)} 个景点")


async def example_3_cross_platform_search():
    """
    示例3: 跨平台并行搜索

    场景: 在不同平台同时搜索同一主题
    """
    logger.info("=" * 60)
    logger.info("示例3: 跨平台并行搜索")
    logger.info("=" * 60)

    keyword = "北京旅游攻略"

    tasks = [
        f"在小红书搜索'{keyword}'，提取第一个结果",
        f"访问知乎 https://www.zhihu.com 搜索'{keyword}'，提取第一个问题标题",
        f"访问百度 https://www.baidu.com 搜索'{keyword}'，提取前3个搜索结果标题"
    ]

    results = await BrowserUseScraper.run_parallel(
        tasks=tasks,
        max_steps=20,
        headless=False
    )

    # 对比不同平台的结果
    for result in results:
        logger.info(f"平台任务 {result['task_index']}: {result['status']}")


async def example_4_performance_comparison():
    """
    示例4: 串行 vs 并行性能对比

    对比串行执行和并行执行的时间差异
    """
    logger.info("=" * 60)
    logger.info("示例4: 串行 vs 并行性能对比")
    logger.info("=" * 60)

    import time

    tasks = [
        "访问小红书搜索'北京'，提取第一个结果",
        "访问小红书搜索'上海'，提取第一个结果",
        "访问小红书搜索'广州'，提取第一个结果"
    ]

    # 方案1: 串行执行
    logger.info("📊 测试方案1: 串行执行")
    start = time.time()

    for idx, task in enumerate(tasks, 1):
        scraper = BrowserUseScraper(headless=True, fast_mode=True)
        try:
            result = await scraper.scrape_with_task(task, max_steps=10)
            logger.info(f"  任务{idx}: {result['status']}")
        finally:
            await scraper.close()

    serial_time = time.time() - start
    logger.info(f"串行执行耗时: {serial_time:.1f}秒")

    # 方案2: 并行执行
    logger.info("📊 测试方案2: 并行执行")
    start = time.time()

    results = await BrowserUseScraper.run_parallel(
        tasks=tasks,
        max_steps=10,
        headless=True,
        fast_mode=True
    )

    parallel_time = time.time() - start
    logger.info(f"并行执行耗时: {parallel_time:.1f}秒")

    # 对比
    speedup = serial_time / parallel_time if parallel_time > 0 else 0
    logger.info(f"🚀 速度提升: {speedup:.1f}x")


async def example_5_error_handling():
    """
    示例5: 并行任务的错误处理

    场景: 部分任务失败不影响其他任务
    """
    logger.info("=" * 60)
    logger.info("示例5: 并行任务错误处理")
    logger.info("=" * 60)

    tasks = [
        "访问小红书搜索'北京'，提取数据",
        "访问一个不存在的网站 https://invalid-url-12345.com",  # 故意失败
        "访问小红书搜索'上海'，提取数据"
    ]

    results = await BrowserUseScraper.run_parallel(
        tasks=tasks,
        max_steps=10,
        headless=True
    )

    # 分析结果
    for result in results:
        status_icon = "✅" if result['status'] == 'success' else "❌"
        logger.info(f"{status_icon} 任务 {result['task_index']}: {result['status']}")

        if result['status'] != 'success':
            logger.warning(f"  错误详情: {result.get('error', 'Unknown')}")


async def example_6_resource_optimization():
    """
    示例6: 资源优化策略

    场景: 根据系统资源动态调整并行数量
    """
    logger.info("=" * 60)
    logger.info("示例6: 资源优化策略")
    logger.info("=" * 60)

    # 假设有10个景点需要爬取
    all_attractions = [
        "北京故宫", "长城", "颐和园", "天坛", "圆明园",
        "上海外滩", "东方明珠", "豫园", "南京路", "城隍庙"
    ]

    # 策略: 每次并行3个（根据系统内存和CPU调整）
    batch_size = 3
    all_results = []

    for i in range(0, len(all_attractions), batch_size):
        batch = all_attractions[i:i + batch_size]
        logger.info(f"🔄 处理第 {i // batch_size + 1} 批: {batch}")

        tasks = [
            f"在小红书搜索'{attr}'，提取第一个笔记标题"
            for attr in batch
        ]

        batch_results = await BrowserUseScraper.run_parallel(
            tasks=tasks,
            max_steps=10,
            headless=True,
            fast_mode=True
        )

        all_results.extend(batch_results)

        # 批次间休息（可选）
        if i + batch_size < len(all_attractions):
            logger.info("⏸️  批次间休息5秒...")
            await asyncio.sleep(5)

    logger.info(f"✅ 全部完成: {len(all_results)} 个任务")


async def main():
    """主函数：运行所有示例"""
    examples = [
        ("基础并行执行", example_1_basic_parallel),
        ("并行爬取多个景点", example_2_multi_attraction_scraping),
        ("跨平台并行搜索", example_3_cross_platform_search),
        ("性能对比", example_4_performance_comparison),
        ("错误处理", example_5_error_handling),
        ("资源优化", example_6_resource_optimization),
    ]

    logger.info("🎯 Browser-Use Parallel Agents 示例集")
    logger.info(f"共 {len(examples)} 个示例\n")

    for idx, (name, func) in enumerate(examples, 1):
        logger.info(f"\n{'='*60}")
        logger.info(f"运行示例 {idx}/{len(examples)}: {name}")
        logger.info(f"{'='*60}\n")

        try:
            await func()
            logger.info(f"✅ 示例 {idx} 完成\n")
        except Exception as e:
            logger.exception(f"❌ 示例 {idx} 失败: {e}\n")

        # 示例间间隔
        await asyncio.sleep(2)

    logger.info("🎉 所有示例运行完成")


if __name__ == "__main__":
    # 运行所有示例
    asyncio.run(main())

    # 或者单独运行某个示例
    # asyncio.run(example_1_basic_parallel())
