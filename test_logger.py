"""快速测试新的日志系统"""
from app.utils.logger import setup_logger, log_function_call, log_step, log_api_call

# 测试 scrapers 模块日志
logger_scraper = setup_logger("app.scrapers.test_scraper")

logger_scraper.info("========== 测试 Scrapers 日志 ==========")
log_step(1, "初始化爬虫", target="测试景点")
log_step(2, "开始爬取数据", max_items=10)
logger_scraper.debug("这是DEBUG级别日志")
logger_scraper.info("这是INFO级别日志")
logger_scraper.warning("这是WARNING级别日志")
log_api_call("测试API", request_data={"query": "test"}, response_data={"result": "success"}, status="success")

# 测试 agents 模块日志
logger_agent = setup_logger("app.agents.test_agent")
logger_agent.info("========== 测试 Agents 日志 ==========")
log_step(1, "创建规划", destination="北京")
log_step(2, "生成行程", days=3)

# 测试函数调用装饰器
@log_function_call
def test_sync_function(param1, param2="default"):
    """测试同步函数"""
    logger_agent.info(f"执行中: param1={param1}, param2={param2}")
    return "sync_result"

@log_function_call
async def test_async_function(param1):
    """测试异步函数"""
    logger_agent.info(f"异步执行中: param1={param1}")
    return "async_result"

# 调用测试函数
test_sync_function("value1", param2="value2")

import asyncio
asyncio.run(test_async_function("async_value"))

print("\n✅ 日志测试完成!")
print("\n📂 日志文件位置:")
print("  - logs/scrapers/test_scraper_20251005.log")
print("  - logs/agents/test_agent_20251005.log")
print("\n💡 请查看日志文件验证以下特性:")
print("  ✓ 模块化目录（scrapers/agents/）")
print("  ✓ 文件名:行号")
print("  ✓ 函数名")
print("  ✓ STEP标记")
print("  ✓ ENTER/EXIT标记")
print("  ✓ API调用追踪")
