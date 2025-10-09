"""基于 loguru 的增强日志系统

特性：
- 统一目录存储，文件名前缀区分模块（如 scrapers_xhs_scraper_20251009.log）
- 支持全局回调（所有 logger 共享，如前端显示）
- 支持局部回调（特定 logger 独有，如模块专用的日志文件）
- 自动包含文件名、行号、函数名
- 彩色控制台输出
- 日志轮转和压缩
- 异常追踪
"""
import os
import sys
from pathlib import Path
from typing import Optional, Callable, Dict
from loguru import logger

# 日志根目录（统一存储，不再分子目录）
LOG_ROOT_DIR = Path("logs")

# 确保日志根目录存在
LOG_ROOT_DIR.mkdir(parents=True, exist_ok=True)


# ==================== 全局回调管理器 ====================

class GlobalCallbackManager:
    """
    全局回调管理器（单例模式）

    特性：
    - 管理所有 logger 共享的全局回调（如前端显示、监控告警）
    - 自动注入到 loguru 的 handler 中
    - 线程安全

    使用场景：
        # 前端注册回调（所有日志都会触发）
        add_global_callback("frontend", streamlit_callback)

        # 清理回调
        remove_global_callback("frontend")
    """

    _instance: Optional["GlobalCallbackManager"] = None
    _callbacks: Dict[str, Callable[[str], None]] = {}

    def __new__(cls):
        """单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._callbacks = {}
        return cls._instance

    def add_callback(self, name: str, callback: Callable[[str], None]):
        """
        注册全局回调

        Args:
            name: 回调名称（如 "frontend", "monitoring"）
            callback: 回调函数，接收日志消息字符串
        """
        self._callbacks[name] = callback
        logger.info(f"✓ 全局回调已注册: {name}")

    def remove_callback(self, name: str):
        """移除全局回调"""
        if name in self._callbacks:
            del self._callbacks[name]
            logger.info(f"✓ 全局回调已移除: {name}")

    def clear_callbacks(self):
        """清空所有全局回调"""
        self._callbacks.clear()
        logger.info("✓ 所有全局回调已清空")

    def trigger(self, message: str):
        """触发所有全局回调（内部使用）"""
        for callback in self._callbacks.values():
            try:
                callback(message)
            except Exception as e:
                # 回调失败不影响主流程
                logger.warning(f"⚠️  全局回调执行失败: {e}")


# 全局单例实例
_global_callback_manager = GlobalCallbackManager()


# ==================== 公共 API ====================

def add_global_callback(name: str, callback: Callable[[str], None]):
    """
    注册全局日志回调（所有 logger 共享）

    Args:
        name: 回调名称（如 "frontend"）
        callback: 回调函数，接收日志消息字符串

    使用示例：
        def streamlit_callback(msg: str):
            st.session_state.logs.append(msg)

        add_global_callback("frontend", streamlit_callback)
    """
    _global_callback_manager.add_callback(name, callback)


def remove_global_callback(name: str):
    """移除全局回调"""
    _global_callback_manager.remove_callback(name)


def clear_global_callbacks():
    """清空所有全局回调"""
    _global_callback_manager.clear_callbacks()


# ==================== 日志文件命名 ====================

def _get_log_prefix(module_name: str) -> str:
    """
    根据模块名生成日志文件前缀

    示例：
        app.scrapers.xhs_scraper → scrapers_xhs_scraper
        app.agents.planner_agent → agents_planner_agent
        frontend.app → frontend_app
        app.utils.logger → utils_logger
    """
    # 移除 app. 前缀
    if module_name.startswith('app.'):
        module_name = module_name[4:]

    # 替换点号为下划线
    return module_name.replace('.', '_')


# ==================== setup_logger ====================

# 用于记录是否已经初始化过基础 handlers（控制台、文件、全局回调）
_initialized = False


def setup_logger(
    name: str,
    level: Optional[str] = None,
    local_callback: Optional[Callable[[str], None]] = None
):
    """
    设置增强的日志记录器

    特性：
    - 统一目录存储（logs/），文件名前缀区分模块
    - 文件日志包含：时间、模块、[文件:行号]、函数名、级别、消息
    - 控制台彩色输出
    - 自动日志轮转（500MB/文件，保留10个文件）
    - 日志压缩（zip格式）
    - ✨ 全局回调：所有 logger 共享（如前端显示），使用 add_global_callback() 注册
    - ✨ 局部回调：仅此 logger 独有（如模块专用日志处理），通过 local_callback 参数传入

    Args:
        name: 模块名（通常传入 __name__）
        level: 日志级别（DEBUG/INFO/WARNING/ERROR），None则从环境变量读取
        local_callback: 局部回调函数（可选），仅对当前 logger 生效

    Returns:
        绑定了模块名的 loguru logger 实例

    使用示例：
        # 基础用法
        logger = setup_logger(__name__)
        logger.info("开始处理")

        # 使用局部回调（仅此 logger 触发）
        def my_local_callback(msg: str):
            print(f"[LOCAL] {msg}")

        logger = setup_logger(__name__, local_callback=my_local_callback)
        logger.info("这条日志会触发局部回调")

    日志文件示例：
        logs/scrapers_xhs_scraper_20251009.log
        logs/agents_planner_agent_20251009.log
        logs/frontend_app_20251009.log
    """
    global _initialized

    # 从环境变量读取日志级别
    if level is None:
        level = os.getenv("LOG_LEVEL", "INFO").upper()

    # 只在第一次调用时初始化基础 handlers
    if not _initialized:
        # loguru 使用全局单例，因此只需配置一次
        # 移除默认的 handler
        logger.remove()

        # === 1. 控制台输出（彩色、简洁格式）===
        logger.add(
            sys.stdout,
            colorize=True,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
            level=level,
        )

        # === 2. 全局回调（所有 logger 共享）===
        """
        创建一个 loguru handler，用于触发全局回调

        Args:
            level: 日志级别（如 "INFO"）
        """

        def callback_sink(message):
            """将日志消息触发全局回调"""
            # message.record 是 loguru 的日志记录对象
            log_msg = message.record["message"]
            _global_callback_manager.trigger(log_msg)

        logger.add(
            callback_sink,
            format="{message}",  # 只传递消息内容
            level=level,
            filter=lambda record: True  # 所有日志都触发
        )

        _initialized = True

    # === 3. 文件输出（详细格式，包含代码行号）- 每个模块独立 ===
    # 生成文件前缀（如 scrapers_xhs_scraper）
    log_prefix = _get_log_prefix(name)

    # 文件路径：logs/模块前缀_日期.log
    log_file = LOG_ROOT_DIR / f"{log_prefix}_{{time:YYYYMMDD}}.log"

    logger.add(
        str(log_file),
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name} | [{file}:{line}] | {function}() | {message}",
        level="DEBUG",  # 文件记录所有级别
        rotation="500 MB",  # 文件大小超过500MB时轮转
        retention=10,  # 保留最近10个日志文件
        compression="zip",  # 压缩旧日志
        encoding="utf-8",
        enqueue=True,  # 异步写入，提高性能
        filter=lambda record: record["extra"].get("name") == name  # 只记录当前模块的日志
    )

    # === 4. 局部回调（仅此 logger 独有）===
    if local_callback:
        def local_callback_sink(message):
            """触发局部回调"""
            # 只处理当前模块的日志
            if message.record["extra"].get("name") == name:
                log_msg = message.record["message"]
                try:
                    local_callback(log_msg)
                except Exception as e:
                    logger.warning(f"⚠️  局部回调执行失败: {e}")

        logger.add(
            local_callback_sink,
            format="{message}",
            level=level
        )

    # 绑定模块名称到logger
    return logger.bind(name=name)


# ==================== 便捷函数 ====================

def log_step(step_num: int, description: str, **details):
    """
    记录流程步骤（带步骤编号和emoji标记）

    ✨ 自动触发全局回调（如前端显示）

    用法：
        from app.utils.logger import log_step

        log_step(1, "访问小红书网站", url="https://xiaohongshu.com")
        log_step(2, "等待页面加载", wait_time=3)
        log_step(3, "点击搜索按钮")

    Args:
        step_num: 步骤编号
        description: 步骤描述
        **details: 额外的详细信息（会以 key=value 格式显示）
    """
    detail_str = ", ".join([f"{k}={v}" for k, v in details.items()]) if details else ""
    msg = f"📍 STEP {step_num}: {description}"
    if detail_str:
        msg += f" | {detail_str}"

    logger.info(msg)


# ==================== 导出 ====================

__all__ = [
    'setup_logger',
    'log_step',
    'logger',  # 直接导出 loguru.logger 供高级用法
    'LOG_ROOT_DIR',  # 导出日志根目录常量
    'add_global_callback',  # 注册全局回调
    'remove_global_callback',  # 移除全局回调
    'clear_global_callbacks',  # 清空全局回调
]
