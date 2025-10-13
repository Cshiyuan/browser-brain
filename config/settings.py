"""配置管理"""
import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


class Settings:
    """应用配置"""

    # 项目根目录
    BASE_DIR = Path(__file__).parent.parent

    # Browser-Use Cloud API配置
    BROWSER_USE_API_KEY: Optional[str] = os.getenv("BROWSER_USE_API_KEY")
    BROWSER_USE_CLOUD: bool = os.getenv("BROWSER_USE_CLOUD", "false").lower() == "true"

    # LLM配置
    GOOGLE_API_KEY: Optional[str] = os.getenv("GOOGLE_API_KEY")
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    ANTHROPIC_API_KEY: Optional[str] = os.getenv("ANTHROPIC_API_KEY")
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "google")  # google, openai, or anthropic
    LLM_MODEL: str = os.getenv("LLM_MODEL", "gemini-2.5-flash")

    # 浏览器配置
    HEADLESS: bool = os.getenv("HEADLESS", "false").lower() == "true"  # 默认显示浏览器
    MAX_CONCURRENT_BROWSERS: int = int(os.getenv("MAX_CONCURRENT_BROWSERS", "3"))

    # 爬虫配置
    XHS_MAX_NOTES: int = int(os.getenv("XHS_MAX_NOTES", "10"))
    MAX_SCRAPE_TIMEOUT: int = int(os.getenv("MAX_SCRAPE_TIMEOUT", "300"))  # AI爬取最大超时(秒)

    # 代理配置
    PROXY_URL: Optional[str] = os.getenv("PROXY_URL")

    # 日志配置
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    # 数据库配置
    DB_PATH: Path = BASE_DIR / os.getenv("DB_PATH", "data/db/travel_planner.db")
    CACHE_DIR: Path = BASE_DIR / os.getenv("CACHE_DIR", "data/cache")

    # 确保目录存在
    @classmethod
    def ensure_dirs(cls):
        """确保必要的目录存在"""
        cls.DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        cls.CACHE_DIR.mkdir(parents=True, exist_ok=True)
        (cls.BASE_DIR / "logs").mkdir(exist_ok=True)


# 创建全局配置实例
settings = Settings()
settings.ensure_dirs()
