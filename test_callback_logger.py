"""测试日志系统的全局回调和局部回调"""

from app.utils.logger import setup_logger, add_global_callback, remove_global_callback


def test_global_callback():
    """测试全局回调（所有 logger 共享）"""
    print("\n" + "=" * 60)
    print("测试 1: 全局回调（所有 logger 共享）")
    print("=" * 60)

    # 定义全局回调函数
    global_logs = []

    def global_callback(msg: str):
        global_logs.append(f"[GLOBAL] {msg}")
        print(f"  ✓ 全局回调触发: {msg}")

    # 注册全局回调
    add_global_callback("test_global", global_callback)

    # 创建两个不同的 logger
    logger1 = setup_logger("module1")
    logger2 = setup_logger("module2")

    # 测试两个 logger 的日志都会触发全局回调
    print("\n📝 Logger1 输出:")
    logger1.info("这是 module1 的日志")

    print("\n📝 Logger2 输出:")
    logger2.info("这是 module2 的日志")

    # 验证
    print(f"\n✅ 全局回调收集到 {len(global_logs)} 条日志:")
    for log in global_logs:
        print(f"  - {log}")

    # 清理
    remove_global_callback("test_global")
    print("\n🧹 全局回调已移除")


def test_local_callback():
    """测试局部回调（仅特定 logger 触发）"""
    print("\n" + "=" * 60)
    print("测试 2: 局部回调（仅特定 logger 触发）")
    print("=" * 60)

    # 定义局部回调函数
    local_logs = []

    def local_callback(msg: str):
        local_logs.append(f"[LOCAL] {msg}")
        print(f"  ✓ 局部回调触发: {msg}")

    # 创建带局部回调的 logger
    logger_with_local = setup_logger("module_with_local", local_callback=local_callback)

    # 创建不带局部回调的 logger
    logger_without_local = setup_logger("module_without_local")

    # 测试
    print("\n📝 带局部回调的 Logger 输出:")
    logger_with_local.info("这是带局部回调的日志")

    print("\n📝 不带局部回调的 Logger 输出:")
    logger_without_local.info("这是不带局部回调的日志")

    # 验证
    print(f"\n✅ 局部回调收集到 {len(local_logs)} 条日志（应该只有1条）:")
    for log in local_logs:
        print(f"  - {log}")


def test_combined_callbacks():
    """测试全局回调 + 局部回调组合"""
    print("\n" + "=" * 60)
    print("测试 3: 全局回调 + 局部回调组合")
    print("=" * 60)

    # 定义全局回调
    global_logs = []

    def global_callback(msg: str):
        global_logs.append(msg)
        print(f"  🌍 全局回调: {msg}")

    # 定义局部回调
    local_logs = []

    def local_callback(msg: str):
        local_logs.append(msg)
        print(f"  📍 局部回调: {msg}")

    # 注册全局回调
    add_global_callback("test_combined", global_callback)

    # 创建带局部回调的 logger
    logger_combined = setup_logger("module_combined", local_callback=local_callback)

    # 测试（应该同时触发全局回调和局部回调）
    print("\n📝 组合 Logger 输出:")
    logger_combined.info("这是组合日志")

    # 验证
    print(f"\n✅ 全局回调收集到 {len(global_logs)} 条日志")
    print(f"✅ 局部回调收集到 {len(local_logs)} 条日志")

    # 清理
    remove_global_callback("test_combined")
    print("\n🧹 全局回调已移除")


def test_cleanup():
    """测试回调清理"""
    print("\n" + "=" * 60)
    print("测试 4: 回调清理")
    print("=" * 60)

    # 注册多个全局回调
    def callback1(msg):
        print(f"  [Callback1] {msg}")

    def callback2(msg):
        print(f"  [Callback2] {msg}")

    add_global_callback("cb1", callback1)
    add_global_callback("cb2", callback2)

    logger = setup_logger("module_cleanup")

    print("\n📝 注册2个全局回调后输出:")
    logger.info("测试消息")

    # 移除一个回调
    print("\n🧹 移除 Callback1:")
    remove_global_callback("cb1")

    print("\n📝 移除1个回调后输出:")
    logger.info("测试消息")

    # 移除所有回调
    print("\n🧹 移除 Callback2:")
    remove_global_callback("cb2")

    print("\n📝 移除所有回调后输出:")
    logger.info("测试消息（不会触发回调）")


def main():
    """运行所有测试"""
    print("🔬 开始测试日志系统...")

    test_global_callback()
    test_local_callback()
    test_combined_callbacks()
    test_cleanup()

    print("\n" + "=" * 60)
    print("✅ 所有测试完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
