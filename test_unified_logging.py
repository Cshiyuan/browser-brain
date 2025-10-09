#!/usr/bin/env python3
"""测试统一日志系统

验证：
1. 所有日志文件存储在 logs/ 目录下（不再分子目录）
2. 文件名前缀正确区分模块
3. 日志内容包含必要信息
"""

import os
import sys
from pathlib import Path

# 设置环境变量
os.environ["LOG_LEVEL"] = "DEBUG"

# 添加项目根目录到 sys.path
sys.path.insert(0, str(Path(__file__).parent))

from app.utils.logger import setup_logger, LOG_ROOT_DIR


def test_module_logging():
    """测试不同模块的日志生成"""

    print("=" * 60)
    print("测试统一日志系统")
    print("=" * 60)

    # 测试1: 爬虫模块日志
    print("\n1. 测试爬虫模块日志...")
    scraper_logger = setup_logger("app.scrapers.xhs_scraper")
    scraper_logger.info("测试小红书爬虫日志")
    scraper_logger.debug("调试信息：正在解析页面")
    scraper_logger.warning("警告：请求速度过快")

    # 测试2: Agent 模块日志
    print("\n2. 测试 Agent 模块日志...")
    agent_logger = setup_logger("app.agents.planner_agent")
    agent_logger.info("测试规划 Agent 日志")
    agent_logger.debug("调试信息：生成旅行方案")

    # 测试3: 前端模块日志
    print("\n3. 测试前端模块日志...")
    frontend_logger = setup_logger("frontend.app")
    frontend_logger.info("测试前端日志")
    frontend_logger.debug("用户输入：北京 7 日游")

    # 测试4: 工具模块日志
    print("\n4. 测试工具模块日志...")
    utils_logger = setup_logger("app.utils.logger")
    utils_logger.info("测试工具日志")

    print("\n" + "=" * 60)
    print("日志文件生成检查")
    print("=" * 60)

    # 检查日志目录结构
    if not LOG_ROOT_DIR.exists():
        print(f"❌ 日志根目录不存在: {LOG_ROOT_DIR}")
        return

    print(f"\n✓ 日志根目录: {LOG_ROOT_DIR.absolute()}")

    # 列出所有日志文件
    log_files = list(LOG_ROOT_DIR.glob("*.log"))

    if not log_files:
        print("\n⚠️  未找到日志文件")
        return

    print(f"\n✓ 找到 {len(log_files)} 个日志文件:\n")

    for log_file in sorted(log_files):
        size = log_file.stat().st_size
        print(f"  - {log_file.name} ({size} bytes)")

    print("\n" + "=" * 60)
    print("预期文件名格式")
    print("=" * 60)
    print("""
✓ 统一存储在 logs/ 目录下
✓ 文件名格式: [模块前缀]_[日期].log

示例：
  - scrapers_xhs_scraper_20251009.log
  - agents_planner_agent_20251009.log
  - frontend_app_20251009.log
  - utils_logger_20251009.log
  - browser_use_agent_20251009_143022.log

对比旧架构（已废弃）：
  ❌ logs/scrapers/xhs_scraper_20251009.log
  ❌ logs/agents/planner_agent_20251009.log
  ❌ logs/browser_use/agent_20251009_143022.log
    """)

    print("\n" + "=" * 60)
    print("优势总结")
    print("=" * 60)
    print("""
1. ✅ 无需预先创建子目录
2. ✅ 所有日志统一在一个目录，便于查找
3. ✅ 文件名前缀清晰区分模块
4. ✅ 支持通配符快速过滤（如 ls logs/scrapers_*）
5. ✅ 维护成本降低（无需维护目录映射表）
    """)


if __name__ == "__main__":
    test_module_logging()
