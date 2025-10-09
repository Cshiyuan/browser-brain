#!/usr/bin/env python3
"""测试logger自动回调功能

验证：
1. setup_logger 返回的 logger 自动触发 LogManager 回调
2. 回调函数接收到所有日志消息
3. 不影响原有的文件和控制台输出
"""

from app.utils.logger import setup_logger, glogger

def test_logger_callbacks():
    """测试 logger 自动回调"""
    print("=" * 60)
    print("测试 Logger 自动回调功能")
    print("=" * 60)

    # 1. 注册回调
    received_messages = []

    def frontend_callback(msg):
        """模拟前端回调"""
        received_messages.append(("frontend", msg))

    glogger.register_callback("frontend", frontend_callback)
    print("\n✓ 已注册前端回调")

    # 2. 创建多个模块的 logger
    logger1 = setup_logger("app.scrapers.xhs_scraper")
    logger2 = setup_logger("app.agents.planner_agent")

    print("\n✓ 创建了2个logger实例")

    # 3. 测试日志输出
    print("\n--- 开始测试日志输出 ---")

    logger1.info("爬虫开始执行")
    logger1.warning("检测到反爬虫")
    logger2.info("生成旅行方案")
    logger2.error("API调用失败")

    print("--- 日志输出完成 ---\n")

    # 4. 验证回调是否收到消息
    print(f"回调接收到 {len(received_messages)} 条消息：")
    for source, msg in received_messages:
        print(f"  [{source}] {msg[:50]}...")

    # 5. 验证结果
    expected_count = 4
    if len(received_messages) == expected_count:
        print(f"\n✅ 测试通过！回调正确接收了 {expected_count} 条消息")
        return True
    else:
        print(f"\n❌ 测试失败！预期 {expected_count} 条，实际 {len(received_messages)} 条")
        return False


def test_log_step():
    """测试 log_step 工具函数"""
    print("\n" + "=" * 60)
    print("测试 log_step 工具函数")
    print("=" * 60)

    from app.utils.logger import log_step

    # 注册回调
    received_messages = []
    glogger.clear_callbacks()  # 清空之前的回调
    glogger.register_callback("test", lambda msg: received_messages.append(msg))

    print("\n--- 测试 log_step ---")
    log_step(1, "初始化浏览器", headless=True)
    log_step(2, "访问目标网站", url="https://example.com")
    log_step(3, "提取数据")

    print(f"\nlog_step 触发了 {len(received_messages)} 条回调")

    if len(received_messages) == 3:
        print("✅ log_step 测试通过！")
        return True
    else:
        print(f"❌ log_step 测试失败！预期 3 条，实际 {len(received_messages)} 条")
        return False


def test_glogger_direct():
    """测试直接使用 glogger"""
    print("\n" + "=" * 60)
    print("测试直接使用 glogger")
    print("=" * 60)

    # 清空并注册新回调
    received_messages = []
    glogger.clear_callbacks()
    glogger.register_callback("test", lambda msg: received_messages.append(msg))

    print("\n--- 使用 glogger 输出日志 ---")
    glogger.info("这是通过 glogger 输出的消息")
    glogger.warning("这是警告")
    glogger.error("这是错误")

    print(f"\nglogger 触发了 {len(received_messages)} 条回调")

    if len(received_messages) == 3:
        print("✅ glogger 测试通过！")
        return True
    else:
        print(f"❌ glogger 测试失败！预期 3 条，实际 {len(received_messages)} 条")
        return False


if __name__ == "__main__":
    # 运行所有测试
    results = []

    results.append(test_logger_callbacks())
    results.append(test_log_step())
    results.append(test_glogger_direct())

    # 总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)

    passed = sum(results)
    total = len(results)

    print(f"通过: {passed}/{total}")

    if all(results):
        print("\n🎉 所有测试通过！Logger自动回调功能正常工作")
        exit(0)
    else:
        print("\n⚠️  部分测试失败")
        exit(1)
