"""配置管理"""
import os
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


class Settings:
    """应用配置"""

    # 项目根目录
    BASE_DIR = Path(__file__).parent.parent

    # LLM配置
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "google")  # google, openai, or anthropic
    LLM_MODEL = os.getenv("LLM_MODEL", "gemini-2.5-flash")

    # 浏览器配置
    HEADLESS = os.getenv("HEADLESS", "false").lower() == "true"  # 默认显示浏览器

    # 爬虫配置
    XHS_MAX_NOTES = int(os.getenv("XHS_MAX_NOTES", "10"))
    MAX_SCRAPE_TIMEOUT = int(os.getenv("MAX_SCRAPE_TIMEOUT", "300"))  # AI爬取最大超时(秒)

    # 日志配置
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

    # 确保目录存在
    @classmethod
    def ensure_dirs(cls):
        """确保必要的目录存在"""
        (cls.BASE_DIR / "logs").mkdir(exist_ok=True)


# 创建全局配置实例
settings = Settings()
settings.ensure_dirs()
