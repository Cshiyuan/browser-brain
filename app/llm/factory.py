"""LLM 工厂类 - 统一管理 LLM 实例化"""
from browser_use import ChatGoogle
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from config.settings import settings
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class LLMFactory:
    """LLM 工厂类 - 根据配置创建不同的 LLM 实例"""

    @staticmethod
    def create_llm():
        """
        根据环境配置创建 LLM 实例

        Returns:
            LLM 实例（ChatGoogle/ChatAnthropic/ChatOpenAI）

        Raises:
            ValueError: 如果 API Key 未设置或 provider 不支持
        """
        provider = settings.LLM_PROVIDER.lower()
        model = settings.LLM_MODEL

        logger.info("📍 初始化 LLM 配置")
        logger.info(f"   🤖 LLM 配置: provider={provider}, model={model}")

        if provider == "google":
            if not settings.GOOGLE_API_KEY:
                logger.error("GOOGLE_API_KEY 未设置")
                raise ValueError("GOOGLE_API_KEY not set in environment")
            logger.info(f"   ✓ 使用 Google Gemini: {model}")
            return ChatGoogle(
                model=model,
                api_key=settings.GOOGLE_API_KEY
            )

        elif provider == "anthropic":
            if not settings.ANTHROPIC_API_KEY:
                logger.error("ANTHROPIC_API_KEY 未设置")
                raise ValueError("ANTHROPIC_API_KEY not set in environment")
            logger.info(f"   ✓ 使用 Anthropic Claude: {model}")
            return ChatAnthropic(
                stop=[],
                model_name=model,
                timeout=None,
                api_key=settings.ANTHROPIC_API_KEY
            )

        elif provider == "openai":
            if not settings.OPENAI_API_KEY:
                logger.error("OPENAI_API_KEY 未设置")
                raise ValueError("OPENAI_API_KEY not set in environment")
            logger.info(f"   ✓ 使用 OpenAI: {model}")
            return ChatOpenAI(
                model=model,
                api_key=settings.OPENAI_API_KEY
            )

        else:
            error_msg = f"不支持的 LLM provider: {provider}. 支持的 provider: google, anthropic, openai"
            logger.error(error_msg)
            raise ValueError(error_msg)
