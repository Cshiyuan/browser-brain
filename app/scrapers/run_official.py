#!/usr/bin/env python3
"""官网收集器独立运行脚本"""
import asyncio
import json
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.scrapers.official_scraper import OfficialScraper
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


async def run_official_scraper(attraction_name: str, xhs_links: list = None, headless: bool = None):
    """
    独立运行官网收集器

    Args:
        attraction_name: 景点名称
        xhs_links: 从小红书提取的链接列表（可选）
        headless: 是否无头模式（None则从配置文件读取）
    """
    logger.info(f"========== 官网收集器独立运行 ==========")
    logger.info(f"景点: {attraction_name}, 参考链接数: {len(xhs_links or [])}, 无头模式: {headless}")

    scraper = OfficialScraper(headless=headless)

    try:
        # 构造模拟的小红书笔记对象（用于传递链接）
        from app.models.attraction import XHSNote
        from datetime import datetime

        mock_notes = []
        if xhs_links:
            # 由于 XHSNote 没有 extracted_links 字段,直接将链接作为内容
            mock_notes = [
                XHSNote(
                    title="参考链接",
                    author="Mock User",
                    content=f"参考链接: {link}",
                    url=link,
                    created_at=datetime.now().isoformat()
                )
                for i, link in enumerate(xhs_links)
            ]

        # 执行爬取
        official_info = await scraper.scrape(attraction_name, mock_notes)

        # 格式化输出
        if official_info:
            result = {
                "attraction": attraction_name,
                "official_info": {
                    "website": official_info.website,
                    "opening_hours": official_info.opening_hours,
                    "ticket_price": official_info.ticket_price,
                    "booking_method": official_info.booking_method,
                    "address": official_info.address,
                    "phone": official_info.phone,
                    "description": official_info.description[:200] + "..." if official_info.description and len(official_info.description) > 200 else official_info.description
                }
            }
            print(json.dumps(result, ensure_ascii=False, indent=2))
            logger.info(f"✅ 成功收集官网信息")
        else:
            result = {
                "attraction": attraction_name,
                "error": "未能获取官网信息"
            }
            print(json.dumps(result, ensure_ascii=False, indent=2))
            logger.warning(f"⚠️  未能获取官网信息")

        return result

    except Exception as e:
        logger.exception(f"❌ 官网收集器执行失败: {e}")
        return {
            "error": str(e),
            "attraction": attraction_name
        }
    finally:
        await scraper.close()
        logger.info(f"========== 官网收集器运行完成 ==========")


def main():
    """命令行入口"""
    import argparse

    parser = argparse.ArgumentParser(description="官网收集器独立运行")
    parser.add_argument("attraction", help="景点名称")
    parser.add_argument("-l", "--links", nargs="*", help="参考链接列表（可选）")
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
    asyncio.run(run_official_scraper(
        attraction_name=args.attraction,
        xhs_links=args.links,
        headless=headless
    ))


if __name__ == "__main__":
    main()
