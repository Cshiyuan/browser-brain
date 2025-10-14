"""基于Browser-Use的AI驱动爬虫基类"""
import asyncio
from typing import Optional, Any, TypeVar, Callable, Dict, List, Literal
from browser_use import Agent, BrowserSession, BrowserProfile
from pydantic import BaseModel
from app.llm import LLMFactory
from app.utils.logger import setup_logger
from app.models.prompts import SystemPrompts
from config.settings import settings

logger = setup_logger(__name__)

# 泛型：批量爬取的返回结果类型
T = TypeVar('T')


class BrowserUseScraper:
    """Browser-Use AI驱动的爬虫基类"""

    def __init__(
        self,
        headless: bool = None,
        fast_mode: bool = False,
        keep_alive: bool = False
    ):
        """
        初始化Browser-Use爬虫
        Args:
            headless: 是否无头模式
            fast_mode: 是否启用快速模式
            keep_alive: 是否保持浏览器会话
        """
        self.headless = headless if headless is not None else settings.HEADLESS
        self.fast_mode = fast_mode
        self.keep_alive = keep_alive
        self.llm = LLMFactory.create_llm()
        self.active_sessions: List[Any] = []  # 追踪活跃的浏览器会话
        self._sessions_lock = asyncio.Lock()  # 并发保护锁



    def create_browser_profile(self, window_config: Optional[Dict] = None) -> BrowserProfile:
        """
        创建浏览器配置
        Args:
            window_config: 可选的窗口配置（window_size, viewport）
        Returns:
            BrowserProfile 对象
        """
        import uuid
        import time
        from pathlib import Path

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
        else:
            # 有头模式：模拟真实用户行为
            browser_args.extend([
                '--start-maximized',  # 最大化窗口（真实用户行为）
            ])
            logger.info("有头模式: 最大化浏览器窗口")

        # Fast Mode优化：减少等待时间以提升速度
        if self.fast_mode:
            wait_page_load = 0.1
            wait_actions = 0.1
            logger.info("🚀 Fast Mode已启用：最小化等待时间")
        else:
            wait_page_load = 2.0
            wait_actions = 1.0
            logger.info("🐢 标准模式：模拟真实用户行为")

        # 浏览器数据存储配置
        browser_data_dir = Path("data/browser")
        browser_data_dir.mkdir(parents=True, exist_ok=True)

        # storage_state：固定路径（保存 cookies）
        storage_state_path = browser_data_dir / "storage_state.json"

        # user_data_dir：随机临时目录
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        user_data_path = browser_data_dir / f"tmp_user_data_{timestamp}_{unique_id}"

        logger.info(f"📁 浏览器存储配置:")
        logger.info(f"   - storage_state: {storage_state_path}")
        logger.info(f"   - user_data_dir: {user_data_path}")

        # 构建配置参数字典
        profile_kwargs = {
            "storage_state": str(storage_state_path),
            "keep_alive": self.keep_alive,
            "headless": self.headless,
            "dom_highlight_elements": True,
            "disable_security": False,
            "user_data_dir": str(user_data_path),
            "args": browser_args,
            "ignore_default_args": ['--enable-automation'],
            "wait_for_network_idle_page_load_time": wait_page_load,
            "wait_between_actions": wait_actions
        }

        # 如果有窗口配置，合并到参数中
        if window_config:
            profile_kwargs.update(window_config)  # type: ignore

        profile = BrowserProfile(**profile_kwargs)  # type: ignore

        mode_desc = "Fast Mode（速度优化）" if self.fast_mode else "标准模式（反检测优化）"
        logger.info(f"✓ 浏览器配置创建完成（{mode_desc}）")
        return profile


    def calculate_window_layout(
        self,
        index: int,
        total_windows: int
    ) -> Optional[Dict]:
        """
        根据窗口总数智能计算窗口布局（有头模式）

        Args:
            index: 当前窗口索引（从0开始）
            total_windows: 同时启动的窗口总数

        Returns:
            窗口配置字典，如果是无头模式则返回 None
        """
        if self.headless:
            return None

        try:
            import screeninfo
            screen = screeninfo.get_monitors()[0]
            screen_width, screen_height = screen.width, screen.height
        except Exception:
            screen_width, screen_height = 1920, 1080

        # 布局参数
        margin = 10
        spacing = 10

        # 根据窗口总数智能计算布局
        import math

        # 优先横向排列，计算最优行列数
        cols = math.ceil(math.sqrt(total_windows * screen_width / screen_height))
        rows = math.ceil(total_windows / cols)

        # 计算窗口尺寸（自适应屏幕）
        window_width = (screen_width - 2 * margin - (cols - 1) * spacing) // cols
        window_height = (screen_height - 2 * margin - (rows - 1) * spacing) // rows

        # 最小尺寸限制（确保窗口可用）
        window_width = max(300, window_width)
        window_height = max(400, window_height)

        # 计算当前窗口的行列位置
        row = index // cols
        col = index % cols

        # 计算窗口偏移量
        x_offset = margin + col * (window_width + spacing)
        y_offset = margin + row * (window_height + spacing)

        # 边界检查
        x_offset = min(x_offset, screen_width - window_width - margin)
        y_offset = min(y_offset, screen_height - window_height - margin)

        logger.debug(
            f"   窗口布局 [{index + 1}/{total_windows}]: "
            f"位置=({x_offset}, {y_offset}), "
            f"尺寸={window_width}x{window_height}, "
            f"网格={rows}行x{cols}列"
        )

        # 注意: window_position 虽然使用 ViewportSize 类型,但 width/height 字段实际代表 x/y 坐标
        # viewport 参数在有头模式下不需要设置(默认 no_viewport=True,内容自适应窗口)
        return {
            "window_size": {"width": window_width, "height": window_height},
            "window_position": {"width": x_offset, "height": y_offset},  # width=x, height=y
        }

    async def scrape_batch(
        self,
        items: List[str],
        scrape_task_fn: Callable[[str], str],
        parse_result_fn: Callable[[Any], T],
        output_model: type[BaseModel],
        max_concurrent: int = 5,
        max_steps: int = 30,
        item_label: str = "item"
    ) -> Dict[str, T]:
        """
        通用批量并发爬取方法

        Args:
            items: 待爬取项目列表（如景点名称列表）
            scrape_task_fn: 生成任务提示词的函数 (item_name -> task_string)
            parse_result_fn: 解析结果的函数 (raw_result -> parsed_result)
            output_model: Pydantic 输出模型
            max_concurrent: 最大并发数
            max_steps: 每个任务的最大步骤数
            item_label: 项目标签（用于日志）

        Returns:
            字典 {item_name: parsed_result}
        """
        logger.info("=" * 60)
        logger.info(f"🚀 开始批量并发爬取")
        logger.info(f"   {item_label}数量: {len(items)}")
        logger.info(f"   最大并发数: {max_concurrent}")
        logger.info("=" * 60)

        # 创建窗口位置池（预先计算好所有位置）
        position_pool: asyncio.Queue = asyncio.Queue()
        for i in range(max_concurrent):
            window_config = self.calculate_window_layout(i, max_concurrent)
            await position_pool.put(window_config)
        logger.info(f"   ✓ 窗口位置池初始化完成（{max_concurrent} 个位置）")

        semaphore = asyncio.Semaphore(max_concurrent)

        async def scrape_with_semaphore(item_name: str):
            """为单个项目爬取（复用 scrape() 方法）"""
            # 从池中借用窗口位置
            window_config = await position_pool.get()
            try:
                async with semaphore:
                    logger.info(f"📍 开始爬取: {item_name}")

                    # 生成任务
                    task = scrape_task_fn(item_name)

                    # 调用 scrape() 方法
                    result = await self.scrape(
                        task=task,
                        output_model=output_model,
                        max_steps=max_steps,
                        use_vision=False,  # 禁用视觉能力以避免截图超时
                        window_config=window_config
                    )

                    # 解析结果
                    if result["status"] == "success" and result.get("is_successful"):
                        parsed_result = parse_result_fn(result["data"])
                        logger.info(f"   ✅ 成功: {item_name}")
                        return item_name, parsed_result
                    else:
                        logger.warning(f"   ❌ 失败: {item_name}")
                        return item_name, None
            finally:
                # 归还窗口位置到池中
                await position_pool.put(window_config)

        # 并发执行
        tasks = [scrape_with_semaphore(name) for name in items]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 汇总结果
        result_dict: Dict[str, T] = {}
        success_count = 0
        fail_count = 0

        for result in results:
            if isinstance(result, Exception):
                logger.error(f"   任务异常: {result}")
                fail_count += 1
            elif isinstance(result, tuple) and len(result) == 2:
                item_name, parsed_data = result
                result_dict[item_name] = parsed_data
                if parsed_data is not None:
                    success_count += 1
                else:
                    fail_count += 1
            else:
                logger.error(f"   结果格式异常: {result}")
                fail_count += 1

        logger.info("=" * 60)
        logger.info(f"✅ 批量爬取完成")
        logger.info(f"   成功: {success_count}, 失败: {fail_count}, 总计: {len(items)}")
        logger.info("=" * 60)

        return result_dict

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
                evaluation = getattr(model_output, 'evaluation_previous_goal', None) or getattr(model_output,
                                                                                                'evaluation', None)
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

    async def scrape(
            self,
            task: str,
            output_model: Optional[type[BaseModel]] = None,
            max_steps: int = 20,
            use_vision: bool | Literal['auto']  = False,  # 默认禁用视觉能力
            window_config: Optional[Dict] = None
    ) -> dict:
        """
        使用Browser-Use Agent执行爬取任务

        Args:
            task: 任务描述（自然语言）
            output_model: Pydantic模型类，用于结构化输出
            max_steps: 最大步骤数
            use_vision: 是否使用视觉能力（截图理解）
            window_config: 窗口配置（批量爬取时传入）

        Returns:
            爬取结果字典
        """
        logger.info(f"📍 STEP 4: 开始AI爬取任务 | max_steps={max_steps}, use_vision={use_vision}")

        logger.info(
            f"任务配置: max_steps={max_steps}, use_vision={use_vision}, output_model={output_model.__name__ if output_model else 'None'}")
        logger.debug(f"完整任务描述:\n{task}")

        # 创建浏览器配置（支持传入窗口配置）
        browser_profile = self.create_browser_profile(window_config)
        browser_session = BrowserSession(browser_profile=browser_profile)

        # 注册浏览器会话到活跃列表（并发安全）
        async with self._sessions_lock:
            self.active_sessions.append(browser_session)

        try:
            logger.info("📍 STEP 5: 创建AI Agent")
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
                agent_kwargs["extend_system_message"] = SystemPrompts.SPEED_OPTIMIZATION
                logger.info("🚀 Fast Mode: flash_mode=True, 速度优化提示词已应用")

            agent = Agent(**agent_kwargs)

            mode_desc = "Fast Mode（速度优先）" if self.fast_mode else "标准模式（质量优先）"
            logger.info(f"   ✓ AI Agent创建成功（{mode_desc}）")

            logger.info(f"📍 STEP 6: 执行AI自动化任务 | timeout={settings.MAX_SCRAPE_TIMEOUT}s")
            logger.info("   🤖 AI开始控制浏览器...")

            # 执行任务
            history = await asyncio.wait_for(
                agent.run(max_steps=max_steps),
                timeout=settings.MAX_SCRAPE_TIMEOUT
            )

            # 提取结果
            result: Any = history.final_result()

            # 收集访问的URL
            visited_urls = [item.state.url for item in history.history if hasattr(item.state, 'url')]

            logger.info(f"   ✅ AI爬取成功，执行了 {len(history.history)} 步")
            logger.info(f"访问的页面: {visited_urls}")

            # 详细记录每一步的执行情况
            self._log_agent_steps(history)

            # 🔧 自动类型转换：如果指定了 output_model，将 JSON 字符串转换为 Pydantic 对象
            if output_model and result:
                try:
                    if isinstance(result, str):
                        # Browser-Use 返回的是 JSON 字符串，自动转换为 Pydantic 对象
                        result = output_model.model_validate_json(result)
                        logger.debug(f"✓ 自动转换 JSON → {output_model.__name__} 对象")
                    elif isinstance(result, dict):
                        # 如果是字典，使用 model_validate
                        result = output_model.model_validate(result)
                        logger.debug(f"✓ 自动转换 dict → {output_model.__name__} 对象")
                    # else: 已经是 Pydantic 对象，无需转换
                except Exception as e:
                    logger.warning(f"⚠️  自动类型转换失败: {e}，返回原始数据")
                    # 转换失败时保持原始数据

            return {
                "is_successful": history.is_successful(),  ### 是否成功
                "status": "success",
                "data": result,  # ← 现在是 Pydantic 对象（如果指定了 output_model）
                "steps": len(history.history),
                "urls": visited_urls,
                "done": history.is_done(),
            }

        except asyncio.TimeoutError:
            logger.error(f"❌ AI爬取超时: {settings.MAX_SCRAPE_TIMEOUT}秒")
            return {
                "is_successful": False,
                "status": "timeout",
                "error": f"Task exceeded {settings.MAX_SCRAPE_TIMEOUT}s timeout"
            }
        except Exception as e:
            logger.exception(f"❌ AI爬取失败: {e}")
            return {
                "is_successful": False,
                "status": "error",
                "error": str(e)
            }
        finally:
            # 关闭浏览器会话
            try:
                await browser_session.stop()
                # 从活跃列表中移除（并发安全）
                async with self._sessions_lock:
                    if browser_session in self.active_sessions:
                        self.active_sessions.remove(browser_session)
                logger.debug("✓ 浏览器会话已关闭")
            except Exception as e:
                logger.warning(f"⚠️  关闭浏览器警告: {e}")

    async def close(self):
        """关闭所有活跃的浏览器会话"""
        if not self.active_sessions:
            logger.debug("无需清理（没有活跃的浏览器会话）")
            return

        # 获取会话副本并清空集合（并发安全）
        async with self._sessions_lock:
            sessions_to_close = list(self.active_sessions)
            self.active_sessions.clear()

        logger.info(f"🧹 关闭 {len(sessions_to_close)} 个浏览器会话...")
        for i, session in enumerate(sessions_to_close, 1):
            try:
                await session.stop()
                logger.debug(f"   ✓ [{i}/{len(sessions_to_close)}] 浏览器会话已关闭")
            except Exception as e:
                logger.warning(f"   ⚠️ [{i}/{len(sessions_to_close)}] 关闭会话警告: {e}")

        logger.info("✅ 浏览器资源清理完成")


