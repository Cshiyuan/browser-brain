"""基于Browser-Use的AI驱动爬虫基类"""
import asyncio
from typing import Optional, List
from pathlib import Path
from browser_use import Agent, BrowserSession, BrowserProfile, ChatGoogle
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from pydantic import BaseModel
from app.utils.logger import (
    setup_logger,
    setup_browser_use_logging,
    log_function_call,
    log_step,
    log_api_call
)
from config.settings import settings

logger = setup_logger(__name__)

# Fast Agent速度优化提示词
SPEED_OPTIMIZATION_PROMPT = """
Speed optimization instructions:
- Be extremely concise and direct in your responses
- Get to the goal as quickly as possible
- Use multi-action sequences whenever possible to reduce steps
- Minimize thinking time and focus on action execution
"""


class BrowserUseScraper:
    """Browser-Use AI驱动的爬虫基类"""

    def __init__(self, headless: bool = None, fast_mode: bool = False, keep_alive: bool = False):
        """
        初始化Browser-Use爬虫

        Args:
            headless: 是否无头模式
            fast_mode: 是否启用快速模式（优化速度）
            keep_alive: 是否保持浏览器会话（用于任务链式执行）
        """
        self.headless = headless if headless is not None else settings.HEADLESS
        self.fast_mode = fast_mode
        self.keep_alive = keep_alive
        self.llm = self._initialize_llm()
        self.browser_session: Optional[BrowserSession] = None
        self.browser_profile = self._create_browser_profile()
        self.current_agent: Optional[Agent] = None  # 用于任务链式执行

        # 设置 browser-use 日志捕获（统一日志管理）
        setup_browser_use_logging()

        if self.keep_alive:
            logger.info("🔗 Keep-Alive模式已启用：浏览器会话将保持活跃")

    def _initialize_llm(self):
        """初始化LLM"""
        log_step(1, "初始化LLM配置")
        provider = settings.LLM_PROVIDER.lower()
        model = settings.LLM_MODEL
        logger.info(f"LLM配置: provider={provider}, model={model}")

        if provider == "google":
            if not settings.GOOGLE_API_KEY:
                logger.error("GOOGLE_API_KEY未设置")
                raise ValueError("GOOGLE_API_KEY not set in environment")
            logger.info(f"✓ 使用 Google Gemini (browser-use ChatGoogle): {model}")
            # 使用 browser-use 内置的 ChatGoogle 类
            return ChatGoogle(
                model=model,
                api_key=settings.GOOGLE_API_KEY
            )
        elif provider == "anthropic":
            if not settings.ANTHROPIC_API_KEY:
                logger.error("ANTHROPIC_API_KEY未设置")
                raise ValueError("ANTHROPIC_API_KEY not set in environment")
            logger.info(f"✓ 使用 Anthropic Claude: {model}")
            return ChatAnthropic(
                model=model,
                api_key=settings.ANTHROPIC_API_KEY
            )
        else:  # default to OpenAI
            if not settings.OPENAI_API_KEY:
                logger.error("OPENAI_API_KEY未设置")
                raise ValueError("OPENAI_API_KEY not set in environment")
            logger.info(f"✓ 使用 OpenAI: {model}")
            return ChatOpenAI(
                model=model,
                api_key=settings.OPENAI_API_KEY
            )

    def _create_browser_profile(self) -> BrowserProfile:
        """创建模拟真实用户的浏览器配置（增强反检测）"""
        log_step(2, "创建浏览器配置", headless=self.headless)

        # 基础反检测参数
        browser_args = [
            '--disable-blink-features=AutomationControlled',  # 隐藏自动化标识
            '--disable-dev-shm-usage',
            '--disable-infobars',  # 隐藏自动化信息栏
        ]

        # 根据有头/无头模式添加不同参数
        if self.headless:
            # 无头模式：添加必要参数
            browser_args.extend([
                '--no-sandbox',
                '--disable-gpu',
                '--window-size=1920,1080',  # 设置窗口大小
            ])
            logger.info("无头模式: 添加额外浏览器参数")
        else:
            # 有头模式：模拟真实用户行为
            browser_args.extend([
                '--start-maximized',  # 最大化窗口（真实用户行为）
            ])
            logger.info("有头模式: 最大化浏览器窗口")

        logger.debug(f"浏览器参数: {browser_args}")

        # 真实的 User-Agent（Mac Chrome）
        user_agent = (
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
            'AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/120.0.0.0 Safari/537.36'
        )

        # Fast Mode优化：减少等待时间以提升速度
        if self.fast_mode:
            wait_page_load = 0.1
            max_page_load = 5.0
            wait_actions = 0.1
            logger.info("🚀 Fast Mode已启用：最小化等待时间")
        else:
            wait_page_load = 2.0
            max_page_load = 10.0
            wait_actions = 1.0
            logger.info("🐢 标准模式：模拟真实用户行为")

        profile = BrowserProfile(
            headless=self.headless,
            disable_security=False,  # 保持安全特性,更像真实浏览器
            user_data_dir=None,
            args=browser_args,
            ignore_default_args=['--enable-automation'],  # 隐藏自动化标识
            wait_for_network_idle_page_load_time=wait_page_load,  # Fast Mode: 0.1s, 标准: 2.0s
            maximum_wait_page_load_time=max_page_load,  # Fast Mode: 5.0s, 标准: 10.0s
            wait_between_actions=wait_actions,  # Fast Mode: 0.1s, 标准: 1.0s
        )

        mode_desc = "Fast Mode（速度优化）" if self.fast_mode else "标准模式（反检测优化）"
        logger.info(f"✓ 浏览器配置创建完成（{mode_desc}）")
        return profile


    def _log_agent_steps(self, history):
        """详细记录 Agent 执行的每一步"""
        logger.info("=" * 60)
        logger.info("🔍 AI Agent 执行步骤详情")
        logger.info("=" * 60)

        for i, step_history in enumerate(history.history, 1):
            logger.info(f"\n📍 Step {i}/{len(history.history)}:")

            # 记录评估结果
            if hasattr(step_history, 'model_output') and step_history.model_output:
                model_output = step_history.model_output

                # 获取评估结果（兼容不同版本的 browser-use）
                evaluation = getattr(model_output, 'evaluation_previous_goal', None) or getattr(model_output, 'evaluation', None)
                if evaluation:
                    logger.info(f"   ⚖️  评估: {evaluation}")

                    # 🔴 检测关键失败原因
                    eval_lower = str(evaluation).lower()
                    if 'security' in eval_lower or 'restriction' in eval_lower:
                        logger.error("   🚫 检测到安全限制（反爬虫拦截）")
                    if 'captcha' in eval_lower:
                        logger.error("   🚫 检测到验证码挑战")
                    if 'failure' in eval_lower or 'failed' in eval_lower:
                        logger.warning("   ⚠️  步骤执行失败")

                # 记录下一步目标（直接从 Pydantic 对象获取属性）
                next_goal = getattr(model_output, 'next_goal', None)
                if next_goal:
                    logger.info(f"   🎯 下一步目标: {next_goal}")

            # 记录执行的动作
            if hasattr(step_history, 'action_result') and step_history.action_result:
                actions = step_history.action_result
                if isinstance(actions, list):
                    for action in actions:
                        action_name = getattr(action, 'action_name', 'unknown')
                        logger.info(f"   🦾 执行动作: {action_name}")
                else:
                    logger.info(f"   🦾 执行动作: {actions}")

            # 记录访问的 URL
            if hasattr(step_history, 'state') and hasattr(step_history.state, 'url'):
                url = step_history.state.url
                logger.info(f"   🔗 当前页面: {url}")

        logger.info("\n" + "=" * 60)

        # 最终结果摘要
        final_result = history.final_result()
        if final_result:
            logger.info(f"📄 最终结果: {final_result}")
        else:
            logger.warning("⚠️  未获取到最终结果")

        logger.info("=" * 60)

    async def _get_browser_session(self) -> BrowserSession:
        """获取或创建BrowserSession实例"""
        if self.browser_session is None:
            log_step(3, "创建浏览器会话", headless=self.headless)
            logger.info(f"正在启动浏览器...")
            self.browser_session = BrowserSession(
                browser_profile=self.browser_profile
            )
            logger.info("✓ 浏览器会话创建成功")
        else:
            logger.debug("复用现有浏览器会话")
        return self.browser_session

    async def scrape_with_task(
        self,
        task: str,
        output_model: Optional[type[BaseModel]] = None,
        max_steps: int = 20,
        use_vision: bool = True
    ) -> dict:
        """
        使用Browser-Use Agent执行爬取任务

        Args:
            task: 任务描述（自然语言）
            output_model: Pydantic模型类，用于结构化输出
            max_steps: 最大步骤数
            use_vision: 是否使用视觉能力（截图理解）

        Returns:
            爬取结果字典
        """
        log_step(4, "开始AI爬取任务", max_steps=max_steps, use_vision=use_vision)

        browser_session = await self._get_browser_session()

        logger.info(f"任务配置: max_steps={max_steps}, use_vision={use_vision}, output_model={output_model.__name__ if output_model else 'None'}")
        logger.debug(f"完整任务描述:\n{task}")

        try:
            log_step(5, "创建AI Agent")

            # Fast Mode优化：添加速度优化提示词和flash_mode
            agent_kwargs = {
                "task": task,
                "llm": self.llm,
                "browser_session": browser_session,
                "output_model_schema": output_model,
                "use_vision": use_vision,
            }

            if self.fast_mode:
                agent_kwargs["flash_mode"] = True  # 禁用LLM thinking以提升速度
                agent_kwargs["extend_system_message"] = SPEED_OPTIMIZATION_PROMPT
                logger.info("🚀 Fast Mode: flash_mode=True, 速度优化提示词已应用")

            agent = Agent(**agent_kwargs)

            mode_desc = "Fast Mode（速度优先）" if self.fast_mode else "标准模式（质量优先）"
            logger.info(f"✓ AI Agent创建成功（{mode_desc}）")

            # 记录API调用
            log_api_call("Browser-Use Agent", request_data={"task": task[:100], "max_steps": max_steps})

            log_step(6, "执行AI自动化任务", timeout=f"{settings.MAX_SCRAPE_TIMEOUT}s")
            logger.info("AI开始控制浏览器...")

            # 执行任务
            history = await asyncio.wait_for(
                agent.run(max_steps=max_steps),
                timeout=settings.MAX_SCRAPE_TIMEOUT
            )

            # 提取结果
            result = history.final_result()

            # 收集访问的URL
            visited_urls = [item.state.url for item in history.history if hasattr(item.state, 'url')]

            logger.info(f"✅ AI爬取成功，执行了 {len(history.history)} 步")
            logger.info(f"访问的页面: {visited_urls}")

            # 详细记录每一步的执行情况
            self._log_agent_steps(history)

            # 记录API响应
            log_api_call("Browser-Use Agent", response_data=result, status="success")

            return {
                "status": "success",
                "data": result,
                "steps": len(history.history),
                "urls": visited_urls
            }

        except asyncio.TimeoutError:
            logger.error(f"❌ AI爬取超时: {settings.MAX_SCRAPE_TIMEOUT}秒")
            log_api_call("Browser-Use Agent", response_data=None, status="timeout")
            return {
                "status": "timeout",
                "error": f"Task exceeded {settings.MAX_SCRAPE_TIMEOUT}s timeout"
            }
        except Exception as e:
            logger.exception(f"❌ AI爬取失败: {e}")
            log_api_call("Browser-Use Agent", response_data=str(e), status="error")
            return {
                "status": "error",
                "error": str(e)
            }

    async def close(self, force: bool = False):
        """
        关闭浏览器会话（修复资源泄漏）

        Args:
            force: 是否强制关闭（忽略keep_alive设置）
        """
        # Keep-Alive模式：除非强制关闭，否则保持会话
        if self.keep_alive and not force:
            logger.info("🔗 Keep-Alive模式：保持浏览器会话，跳过关闭")
            return

        if self.browser_session:
            log_step(7, "关闭浏览器会话")
            try:
                # Browser-Use 0.7.x 使用 stop() 方法而非 close()
                if hasattr(self.browser_session, 'stop'):
                    await self.browser_session.stop()
                    logger.info("✓ 使用 stop() 方法关闭")
                elif hasattr(self.browser_session, 'close'):
                    await self.browser_session.close()
                    logger.info("✓ 使用 close() 方法关闭")

                # 等待资源释放（修复 aiohttp 连接泄漏）
                await asyncio.sleep(0.1)

                logger.info("✅ 浏览器会话已成功关闭")
            except Exception as e:
                # 降级为警告，不影响主流程
                logger.warning(f"⚠️  关闭浏览器时出现警告: {e}")
            finally:
                self.browser_session = None
                logger.debug("浏览器会话对象已清空")

    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self._get_browser_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器退出"""
        await self.close()

    async def run_task_chain(
        self,
        tasks: List[str],
        output_model: Optional[type[BaseModel]] = None,
        max_steps_per_task: int = 20
    ) -> List[dict]:
        """
        链式执行多个任务（保持浏览器会话）

        Args:
            tasks: 任务列表（自然语言描述）
            output_model: Pydantic模型类（可选）
            max_steps_per_task: 每个任务的最大步骤数

        Returns:
            每个任务的执行结果列表

        Example:
            tasks = [
                "搜索'北京故宫'",
                "点击第一个搜索结果",
                "提取页面标题和摘要"
            ]
            results = await scraper.run_task_chain(tasks)
        """
        if not tasks:
            logger.warning("任务列表为空")
            return []

        logger.info(f"🔗 开始链式执行 {len(tasks)} 个任务（Keep-Alive模式）")

        # 确保浏览器会话已启动
        browser_session = await self._get_browser_session()

        results = []

        for idx, task in enumerate(tasks, 1):
            logger.info(f"📍 任务 {idx}/{len(tasks)}: {task[:50]}...")

            try:
                # 第一个任务：创建新Agent
                if idx == 1:
                    log_step(5, f"创建AI Agent（任务{idx}）")

                    agent_kwargs = {
                        "task": task,
                        "llm": self.llm,
                        "browser_session": browser_session,
                        "output_model_schema": output_model,
                        "use_vision": True,
                    }

                    if self.fast_mode:
                        agent_kwargs["flash_mode"] = True
                        agent_kwargs["extend_system_message"] = SPEED_OPTIMIZATION_PROMPT

                    self.current_agent = Agent(**agent_kwargs)
                    logger.info(f"✓ AI Agent创建成功（任务{idx}）")

                else:
                    # 后续任务：添加到现有Agent
                    log_step(5, f"添加新任务到Agent（任务{idx}）")
                    self.current_agent.add_new_task(task)
                    logger.info(f"✓ 任务已添加到Agent（任务{idx}）")

                # 执行任务
                log_step(6, f"执行AI任务{idx}", timeout=f"{settings.MAX_SCRAPE_TIMEOUT}s")
                history = await asyncio.wait_for(
                    self.current_agent.run(max_steps=max_steps_per_task),
                    timeout=settings.MAX_SCRAPE_TIMEOUT
                )

                # 提取结果
                result = history.final_result()
                visited_urls = [item.state.url for item in history.history if hasattr(item.state, 'url')]

                logger.info(f"✅ 任务{idx}完成，执行了 {len(history.history)} 步")
                logger.debug(f"访问的页面: {visited_urls}")

                results.append({
                    "task_index": idx,
                    "task": task,
                    "status": "success",
                    "data": result,
                    "steps": len(history.history),
                    "urls": visited_urls
                })

            except asyncio.TimeoutError:
                logger.error(f"❌ 任务{idx}超时: {settings.MAX_SCRAPE_TIMEOUT}秒")
                results.append({
                    "task_index": idx,
                    "task": task,
                    "status": "timeout",
                    "error": f"Task exceeded {settings.MAX_SCRAPE_TIMEOUT}s timeout"
                })
                break  # 超时后中断链式执行

            except Exception as e:
                logger.exception(f"❌ 任务{idx}失败: {e}")
                results.append({
                    "task_index": idx,
                    "task": task,
                    "status": "error",
                    "error": str(e)
                })
                break  # 失败后中断链式执行

        logger.info(f"🔗 链式任务执行完成: {len(results)}/{len(tasks)} 个任务")

        return results

    @staticmethod
    async def run_parallel(
        tasks: List[str],
        output_model: Optional[type[BaseModel]] = None,
        max_steps: int = 20,
        headless: bool = True,
        use_vision: bool = True,
        fast_mode: bool = False
    ) -> List[dict]:
        """
        并行执行多个独立任务（每个任务使用独立的浏览器实例）

        Args:
            tasks: 任务描述列表（自然语言）
            output_model: Pydantic模型类（可选）
            max_steps: 每个任务的最大步骤数
            headless: 是否使用无头浏览器
            use_vision: 是否启用视觉能力
            fast_mode: 是否启用Fast Mode

        Returns:
            List[dict]: 结果列表，每个包含 {task_index, status, data/error}

        注意：
            - 每个任务使用独立的浏览器实例（避免状态冲突）
            - 使用 asyncio.gather() 实现真正的并发执行
            - 适用于完全独立的多个任务（如爬取多个网站）
            - 资源消耗较高（N个任务 = N个浏览器进程）
        """
        logger.info(f"🚀 并行执行 {len(tasks)} 个任务...")

        async def run_single_task(task_index: int, task: str):
            """执行单个任务（创建独立浏览器实例）"""
            scraper = None
            try:
                # 为每个任务创建独立的爬虫实例
                scraper = BrowserUseScraper(
                    headless=headless,
                    fast_mode=fast_mode,
                    keep_alive=False  # 并行模式不使用Keep-Alive
                )

                logger.info(f"📌 任务 {task_index}: 启动独立浏览器...")

                # 执行任务
                result = await scraper.scrape_with_task(
                    task=task,
                    output_model=output_model,
                    max_steps=max_steps,
                    use_vision=use_vision
                )

                logger.info(f"✅ 任务 {task_index}: 完成 (执行了 {result.get('steps', 0)} 步)")

                return {
                    "task_index": task_index,
                    "task": task,
                    "status": result["status"],
                    "data": result.get("data"),
                    "steps": result.get("steps", 0)
                }

            except Exception as e:
                logger.error(f"❌ 任务 {task_index} 失败: {e}")
                return {
                    "task_index": task_index,
                    "task": task,
                    "status": "error",
                    "error": str(e)
                }

            finally:
                # 确保关闭浏览器
                if scraper:
                    await scraper.close(force=True)

        # 使用 asyncio.gather() 并行执行所有任务
        parallel_tasks = [
            run_single_task(idx, task)
            for idx, task in enumerate(tasks, 1)
        ]

        results = await asyncio.gather(*parallel_tasks, return_exceptions=True)

        # 处理异常结果
        final_results = []
        for idx, result in enumerate(results, 1):
            if isinstance(result, Exception):
                logger.error(f"❌ 任务 {idx} 异常: {result}")
                final_results.append({
                    "task_index": idx,
                    "task": tasks[idx - 1],
                    "status": "exception",
                    "error": str(result)
                })
            else:
                final_results.append(result)

        # 统计结果
        success_count = sum(1 for r in final_results if r["status"] == "success")
        logger.info(
            f"🏁 并行任务完成: {success_count}/{len(tasks)} 个成功"
        )

        return final_results
