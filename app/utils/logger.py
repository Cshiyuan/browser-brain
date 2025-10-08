"""基于 loguru 的增强日志系统

特性：
- 自动按模块分目录存储日志（scrapers/agents/frontend/main）
- 自动包含文件名、行号、函数名
- 彩色控制台输出
- 日志轮转和压缩
- 异常追踪
- 装饰器支持
"""
import os
import sys
import functools
import logging
from pathlib import Path
from typing import Optional, Callable, Any
from loguru import logger


# 日志根目录
LOG_ROOT_DIR = Path("logs")

# 日志目录映射
LOG_DIR_MAPPING = {
    'app.scrapers': 'scrapers',
    'app.agents': 'agents',
    'frontend': 'frontend',
    'app.models': 'models',
    'app.utils': 'utils',
}

# 创建所有日志目录（包括 browser-use 专用目录）
def _ensure_log_directories():
    """确保所有日志目录存在"""
    # 创建根目录
    LOG_ROOT_DIR.mkdir(parents=True, exist_ok=True)

    # 创建所有子目录
    for subdir in LOG_DIR_MAPPING.values():
        (LOG_ROOT_DIR / subdir).mkdir(parents=True, exist_ok=True)

    # 创建 browser-use 专用目录
    (LOG_ROOT_DIR / "browser_use").mkdir(parents=True, exist_ok=True)

    # 创建主日志目录
    (LOG_ROOT_DIR / "main").mkdir(parents=True, exist_ok=True)

# 在模块加载时创建目录
_ensure_log_directories()


def _get_log_subdir(module_name: str) -> str:
    """根据模块名确定日志子目录"""
    for prefix, subdir in LOG_DIR_MAPPING.items():
        if module_name.startswith(prefix):
            return subdir
    return 'main'


def setup_logger(name: str, level: str = None) -> "logger":
    """
    设置增强的日志记录器（基于 loguru）

    特性：
    - 自动按模块分类到不同目录
    - 文件日志包含：时间、模块、[文件:行号]、函数名、级别、消息
    - 控制台彩色输出
    - 自动日志轮转（500MB/文件，保留10个文件）
    - 日志压缩（zip格式）

    Args:
        name: 模块名（通常传入 __name__）
        level: 日志级别（DEBUG/INFO/WARNING/ERROR），None则从环境变量读取

    Returns:
        配置好的 loguru logger 实例（全局单例）

    使用示例：
        logger = setup_logger(__name__)
        logger.info("开始处理")
        logger.debug("详细信息", extra={"user_id": 123})
    """
    # 从环境变量读取日志级别
    if level is None:
        level = os.getenv("LOG_LEVEL", "INFO").upper()

    # loguru 使用全局单例，因此只需配置一次
    # 移除默认的 handler
    logger.remove()

    # === 控制台输出（彩色、简洁格式）===
    logger.add(
        sys.stdout,
        colorize=True,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
        level=level,
    )

    # === 文件输出（详细格式，包含代码行号）===
    log_subdir = _get_log_subdir(name)
    log_dir = LOG_ROOT_DIR / log_subdir

    # 获取模块简称
    module_short_name = name.split('.')[-1]
    log_file = log_dir / f"{module_short_name}_{{time:YYYYMMDD}}.log"

    logger.add(
        str(log_file),
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name} | [{file}:{line}] | {function}() | {message}",
        level="DEBUG",  # 文件记录所有级别
        rotation="500 MB",  # 文件大小超过500MB时轮转
        retention=10,  # 保留最近10个日志文件
        compression="zip",  # 压缩旧日志
        encoding="utf-8",
        enqueue=True,  # 异步写入，提高性能
    )

    # 绑定模块名称到logger
    return logger.bind(name=name)


def log_function_call(func: Optional[Callable] = None):
    """
    装饰器：自动记录函数的进入和退出

    用法：
        from app.utils.logger import setup_logger, log_function_call

        logger = setup_logger(__name__)

        @log_function_call
        async def my_function(arg1, arg2):
            logger.info("处理中...")
            return result

    特性：
    - 自动记录函数进入（ENTER）和退出（EXIT）
    - 记录函数参数（前2个位置参数 + 所有关键字参数的key）
    - 自动捕获并记录异常
    - 支持同步和异步函数
    """
    def decorator(f: Callable) -> Callable:
        @functools.wraps(f)
        async def async_wrapper(*args, **kwargs):
            func_name = f.__qualname__
            # 只记录前2个参数，避免日志过长
            args_repr = f"args={args[:2]}" if args else "args=()"
            kwargs_repr = f"kwargs={list(kwargs.keys())}" if kwargs else "kwargs={}"

            logger.info(f"→ ENTER {func_name} | {args_repr}, {kwargs_repr}")

            try:
                result = await f(*args, **kwargs)
                logger.info(f"← EXIT {func_name} | success")
                return result
            except Exception as e:
                logger.exception(f"← EXIT {func_name} | error: {e}")
                raise

        @functools.wraps(f)
        def sync_wrapper(*args, **kwargs):
            func_name = f.__qualname__
            args_repr = f"args={args[:2]}" if args else "args=()"
            kwargs_repr = f"kwargs={list(kwargs.keys())}" if kwargs else "kwargs={}"

            logger.info(f"→ ENTER {func_name} | {args_repr}, {kwargs_repr}")

            try:
                result = f(*args, **kwargs)
                logger.info(f"← EXIT {func_name} | success")
                return result
            except Exception as e:
                logger.exception(f"← EXIT {func_name} | error: {e}")
                raise

        # 判断是否是协程函数
        import asyncio
        if asyncio.iscoroutinefunction(f):
            return async_wrapper
        else:
            return sync_wrapper

    # 支持 @log_function_call 和 @log_function_call() 两种用法
    if func is None:
        return decorator
    else:
        return decorator(func)


def log_step(step_num: int, description: str, **details):
    """
    记录流程步骤（带步骤编号和emoji标记）

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


def log_api_call(api_name: str, request_data: Any = None, response_data: Any = None, status: str = "success"):
    """
    记录API调用（请求/响应）

    用法：
        from app.utils.logger import log_api_call

        # 记录请求
        log_api_call("Google Gemini API", request_data={"task": "爬取小红书"})

        # 记录响应
        log_api_call("Google Gemini API", response_data=result, status="success")

        # 记录完整调用
        log_api_call("Google Gemini API",
                     request_data={"task": "..."},
                     response_data=result,
                     status="success")

    Args:
        api_name: API名称
        request_data: 请求数据
        response_data: 响应数据
        status: 调用状态（success/error/timeout）
    """
    if request_data is not None:
        # 截断长数据，避免日志过长
        data_str = str(request_data)[:200]
        if len(str(request_data)) > 200:
            data_str += "..."
        logger.debug(f"📤 API REQUEST: {api_name} | {data_str}")

    if response_data is not None:
        data_str = str(response_data)[:200]
        if len(str(response_data)) > 200:
            data_str += "..."

        if status == "success":
            logger.debug(f"📥 API RESPONSE: {api_name} | {data_str}")
        elif status == "error":
            logger.error(f"❌ API ERROR: {api_name} | {data_str}")
        else:
            logger.warning(f"⚠️  API {status.upper()}: {api_name} | {data_str}")


def setup_browser_use_logging():
    """
    配置 browser-use 库的标准日志系统（logging模块）

    browser-use 使用标准 logging 库，此函数将其日志输出到文件。
    调用时机：在创建 BrowserUseScraper 实例时

    使用示例：
        from app.utils.logger import setup_browser_use_logging

        # 在爬虫初始化时调用一次
        setup_browser_use_logging()
    """
    from datetime import datetime

    # 创建带时间戳的日志文件
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = LOG_ROOT_DIR / "browser_use" / f"agent_{timestamp}.log"

    # 获取 browser-use 的根 logger
    browser_use_logger = logging.getLogger('browser_use')
    browser_use_logger.setLevel(logging.DEBUG)

    # 避免重复添加 handler
    if browser_use_logger.handlers:
        return

    # 创建文件处理器
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)

    # 设置格式器
    formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)
    browser_use_logger.addHandler(file_handler)

    # 添加控制台输出（可选）
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    browser_use_logger.addHandler(console_handler)

    logger.info(f"✓ Browser-Use 日志已配置: {log_file}")


# 导出主要接口
__all__ = [
    'setup_logger',
    'setup_browser_use_logging',
    'log_function_call',
    'log_step',
    'log_api_call',
    'logger',  # 直接导出 loguru.logger 供高级用法
    'LOG_ROOT_DIR',  # 导出日志根目录常量
]
