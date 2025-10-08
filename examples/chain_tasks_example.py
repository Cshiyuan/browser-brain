#!/usr/bin/env python3
"""
Browser-Use Chain Agent Tasks 示例

演示如何使用Keep-Alive模式和任务链式执行功能
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.scrapers.xhs_scraper import XHSScraper
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


async def example_1_basic_chain():
    """
    示例1: 基础任务链执行

    场景: 在小红书上搜索并点击第一个结果
    """
    logger.info("=" * 60)
    logger.info("示例1: 基础任务链执行")
    logger.info("=" * 60)

    # 启用Keep-Alive模式
    scraper = XHSScraper(headless=False, keep_alive=True)

    try:
        # 定义任务链
        tasks = [
            "访问小红书网站 https://www.xiaohongshu.com",
            "在搜索框输入'北京故宫'并搜索",
            "提取第一个搜索结果的标题"
        ]

        # 执行任务链
        results = await scraper.run_task_chain(tasks, max_steps_per_task=10)

        # 打印结果
        for result in results:
            logger.info(f"任务{result['task_index']}: {result['status']}")
            if result['status'] == 'success':
                logger.info(f"结果: {result['data']}")

    finally:
        # Keep-Alive模式：需要手动强制关闭
        await scraper.close(force=True)


async def example_2_multi_step_extraction():
    """
    示例2: 多步数据提取

    场景: 搜索 → 点击 → 提取详细信息
    """
    logger.info("=" * 60)
    logger.info("示例2: 多步数据提取")
    logger.info("=" * 60)

    scraper = XHSScraper(
        headless=False,
        keep_alive=True,
        fast_mode=True  # 启用Fast Mode加速
    )

    try:
        tasks = [
            "访问小红书并搜索'北京旅游攻略'",
            "滚动页面加载更多结果",
            "点击第一个笔记进入详情页",
            "提取笔记标题、作者、点赞数和内容摘要"
        ]

        results = await scraper.run_task_chain(tasks, max_steps_per_task=15)

        # 提取最后一步的数据
        if results and results[-1]['status'] == 'success':
            final_data = results[-1]['data']
            logger.info(f"✅ 提取成功: {final_data}")
        else:
            logger.error("❌ 任务链执行失败")

    finally:
        await scraper.close(force=True)


async def example_3_conversational_flow():
    """
    示例3: 对话式交互流程

    场景: 模拟用户对话式查询
    """
    logger.info("=" * 60)
    logger.info("示例3: 对话式交互流程")
    logger.info("=" * 60)

    scraper = XHSScraper(headless=False, keep_alive=True)

    try:
        # 第一轮对话
        logger.info("用户: 搜索北京旅游相关的笔记")
        task1_result = await scraper.run_task_chain([
            "在小红书搜索'北京旅游'"
        ])

        # 第二轮对话（基于上一轮的结果）
        logger.info("用户: 告诉我第一个结果是什么")
        task2_result = await scraper.run_task_chain([
            "提取第一个搜索结果的标题和作者"
        ])

        # 第三轮对话
        logger.info("用户: 点击进去看看详细内容")
        task3_result = await scraper.run_task_chain([
            "点击第一个搜索结果",
            "提取笔记的完整内容"
        ])

        logger.info("✅ 对话式交互完成")

    finally:
        await scraper.close(force=True)


async def example_4_error_handling():
    """
    示例4: 错误处理和降级

    场景: 任务链中某一步失败后的处理
    """
    logger.info("=" * 60)
    logger.info("示例4: 错误处理和降级")
    logger.info("=" * 60)

    scraper = XHSScraper(headless=False, keep_alive=True)

    try:
        # 故意包含一个可能失败的任务
        tasks = [
            "访问小红书网站",
            "搜索'北京故宫'",
            "点击不存在的元素",  # 这一步可能失败
            "提取结果"  # 这一步不会执行
        ]

        results = await scraper.run_task_chain(tasks, max_steps_per_task=10)

        # 分析结果
        success_count = sum(1 for r in results if r['status'] == 'success')
        logger.info(f"✅ 成功: {success_count}/{len(results)} 个任务")

        # 找到失败的任务
        for result in results:
            if result['status'] != 'success':
                logger.error(
                    f"❌ 任务{result['task_index']}失败: "
                    f"{result.get('error', 'Unknown error')}"
                )

    finally:
        await scraper.close(force=True)


async def example_5_keep_alive_comparison():
    """
    示例5: Keep-Alive模式性能对比

    对比使用和不使用Keep-Alive的性能差异
    """
    logger.info("=" * 60)
    logger.info("示例5: Keep-Alive模式性能对比")
    logger.info("=" * 60)

    import time

    tasks = [
        "访问小红书",
        "搜索'测试'",
        "提取第一个结果"
    ]

    # 方案1: 不使用Keep-Alive（每个任务重新启动浏览器）
    logger.info("📊 测试方案1: 标准模式（每次重新启动浏览器）")
    start = time.time()

    for task in tasks:
        scraper = XHSScraper(headless=True, keep_alive=False)
        try:
            result = await scraper.run_task_chain([task], max_steps_per_task=5)
        finally:
            await scraper.close()

    standard_time = time.time() - start
    logger.info(f"标准模式耗时: {standard_time:.1f}秒")

    # 方案2: 使用Keep-Alive（浏览器保持活跃）
    logger.info("📊 测试方案2: Keep-Alive模式")
    start = time.time()

    scraper = XHSScraper(headless=True, keep_alive=True)
    try:
        result = await scraper.run_task_chain(tasks, max_steps_per_task=5)
    finally:
        await scraper.close(force=True)

    keepalive_time = time.time() - start
    logger.info(f"Keep-Alive模式耗时: {keepalive_time:.1f}秒")

    # 对比
    speedup = standard_time / keepalive_time if keepalive_time > 0 else 0
    logger.info(f"🚀 速度提升: {speedup:.1f}x")


async def main():
    """主函数：运行所有示例"""
    examples = [
        ("基础任务链", example_1_basic_chain),
        ("多步数据提取", example_2_multi_step_extraction),
        ("对话式交互", example_3_conversational_flow),
        ("错误处理", example_4_error_handling),
        ("性能对比", example_5_keep_alive_comparison),
    ]

    logger.info("🎯 Browser-Use Chain Agent Tasks 示例集")
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
    # asyncio.run(example_1_basic_chain())
