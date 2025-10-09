"""测试全局日志管理器功能"""
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from app.utils.logger import glogger, setup_logger

# 初始化本地logger
logger = setup_logger(__name__)


def test_basic_logging():
    """测试基础日志功能"""
    print("\n" + "="*60)
    print("测试1: 基础日志功能")
    print("="*60)

    glogger.info("这是一条INFO日志")
    glogger.warning("这是一条WARNING日志")
    glogger.error("这是一条ERROR日志")
    glogger.debug("这是一条DEBUG日志")

    print("✅ 基础日志测试完成\n")


def test_callback_registration():
    """测试回调注册功能"""
    print("="*60)
    print("测试2: 回调注册功能")
    print("="*60)

    # 定义测试回调
    collected_logs = []

    def test_callback(message: str):
        collected_logs.append(message)
        print(f"   [回调捕获] {message}")

    # 注册回调
    glogger.register_callback("test_frontend", test_callback)

    # 发送日志
    glogger.info("测试日志1: 初始化浏览器")
    glogger.info("测试日志2: 开始爬取数据")
    glogger.warning("测试日志3: 检测到反爬虫")
    glogger.error("测试日志4: 爬取失败")

    # 移除回调
    glogger.unregister_callback("test_frontend")

    print(f"\n回调收集到的日志数量: {len(collected_logs)}")
    print("✅ 回调注册测试完成\n")

    return collected_logs


def test_multiple_callbacks():
    """测试多个回调"""
    print("="*60)
    print("测试3: 多个回调同时工作")
    print("="*60)

    # 定义多个回调
    frontend_logs = []
    websocket_logs = []

    def frontend_callback(msg):
        frontend_logs.append(msg)
        print(f"   [前端] {msg}")

    def websocket_callback(msg):
        websocket_logs.append(msg)
        print(f"   [WebSocket] {msg}")

    # 注册多个回调
    glogger.register_callback("frontend", frontend_callback)
    glogger.register_callback("websocket", websocket_callback)

    # 发送日志
    glogger.info("多回调测试日志1")
    glogger.info("多回调测试日志2")

    # 清理
    glogger.clear_callbacks()

    print(f"\n前端收集到: {len(frontend_logs)} 条")
    print(f"WebSocket收集到: {len(websocket_logs)} 条")
    print("✅ 多回调测试完成\n")


def test_step_logging():
    """测试步骤日志"""
    print("="*60)
    print("测试4: 步骤日志功能")
    print("="*60)

    collected_steps = []

    def step_callback(msg):
        collected_steps.append(msg)
        print(f"   [步骤] {msg}")

    glogger.register_callback("step_test", step_callback)

    # 测试步骤日志
    glogger.log_step(1, "初始化浏览器", headless=True)
    glogger.log_step(2, "访问小红书网站", url="https://xiaohongshu.com")
    glogger.log_step(3, "搜索关键词", keyword="北京故宫")

    glogger.unregister_callback("step_test")

    print(f"\n收集到步骤日志: {len(collected_steps)} 条")
    print("✅ 步骤日志测试完成\n")


def test_callback_error_handling():
    """测试回调错误处理"""
    print("="*60)
    print("测试5: 回调错误处理")
    print("="*60)

    def faulty_callback(msg):
        raise ValueError("故意抛出的错误")

    glogger.register_callback("faulty", faulty_callback)

    # 这应该不会中断程序
    glogger.info("测试错误回调")

    glogger.unregister_callback("faulty")

    print("✅ 错误处理测试完成（回调失败不影响主流程）\n")


def main():
    """运行所有测试"""
    print("\n🧪 全局日志管理器测试套件")
    print("="*60)

    test_basic_logging()
    logs = test_callback_registration()
    test_multiple_callbacks()
    test_step_logging()
    test_callback_error_handling()

    print("\n" + "="*60)
    print("🎉 所有测试完成！")
    print("="*60)

    print("\n📊 测试总结:")
    print("   ✅ 基础日志功能")
    print("   ✅ 回调注册/注销")
    print("   ✅ 多回调并发")
    print("   ✅ 步骤日志")
    print("   ✅ 错误处理")

    print("\n💡 使用方法:")
    print("   1. 前端注册回调: glogger.register_callback('frontend', callback_func)")
    print("   2. 模块使用日志: glogger.info('日志消息')")
    print("   3. 清理回调: glogger.unregister_callback('frontend')")


if __name__ == "__main__":
    main()
