#!/usr/bin/env python3
"""小红书收集器独立运行脚本"""
import asyncio
import json
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.scrapers.xhs_scraper import XHSScraper
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


async def run_xhs_scraper(attraction_name: str, max_notes: int = 5, headless: bool = None):
    """
    独立运行小红书收集器

    Args:
        attraction_name: 景点名称
        max_notes: 最大笔记数
        headless: 是否无头模式（None则从配置文件读取）
    """
    logger.info(f"========== 小红书收集器独立运行 ==========")
    logger.info(f"景点: {attraction_name}, 笔记数: {max_notes}, 无头模式: {headless}")

    scraper = XHSScraper(headless=headless)

    try:
        # 执行爬取
        notes = await scraper.scrape(attraction_name, max_notes)

        # 格式化输出
        result = {
            "attraction": attraction_name,
            "total_notes": len(notes),
            "notes": [
                {
                    "note_id": note.note_id,
                    "title": note.title,
                    "author": note.author,
                    "content": note.content[:200] + "..." if len(note.content) > 200 else note.content,
                    "likes": note.likes,
                    "collects": note.collects,
                    "comments": note.comments,
                    "images_count": len(note.images),
                    "extracted_links": note.extracted_links,
                    "keywords": note.keywords,
                    "created_at": note.created_at.isoformat()
                }
                for note in notes
            ]
        }

        # 打印JSON结果
        print(json.dumps(result, ensure_ascii=False, indent=2))

        logger.info(f"✅ 成功收集 {len(notes)} 条小红书笔记")
        return result

    except Exception as e:
        logger.exception(f"❌ 小红书收集器执行失败: {e}")
        return {
            "error": str(e),
            "attraction": attraction_name
        }
    finally:
        await scraper.close()
        logger.info(f"========== 小红书收集器运行完成 ==========")


def main():
    """命令行入口"""
    import argparse

    parser = argparse.ArgumentParser(description="小红书收集器独立运行")
    parser.add_argument("attraction", help="景点名称")
    parser.add_argument("-n", "--max-notes", type=int, default=5, help="最大笔记数（默认5）")
    parser.add_argument("--no-headless", action="store_true", help="显示浏览器界面（强制有头模式）")
    parser.add_argument("--headless", action="store_true", help="无头模式（强制无头模式）")

    args = parser.parse_args()

    # 确定 headless 参数
    # 优先级：命令行参数 > 配置文件默认值
    if args.no_headless:
        headless = False  # 强制有头模式
    elif args.headless:
        headless = True   # 强制无头模式
    else:
        headless = None   # 使用配置文件默认值（.env 中的 HEADLESS）

    # 运行收集器
    asyncio.run(run_xhs_scraper(
        attraction_name=args.attraction,
        max_notes=args.max_notes,
        headless=headless
    ))


if __name__ == "__main__":
    main()
