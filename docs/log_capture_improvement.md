# 日志捕获改进方案 - 实施完成

**完成时间**: 2025-10-07
**状态**: ✅ 已实施并测试通过

---

## 🎯 问题描述

之前的日志系统存在以下问题：

### ❌ 原始问题

1. **Browser-Use 的详细日志未被捕获**
   - AI Agent 的执行步骤只输出到终端
   - 应用日志文件中看不到详细的失败原因
   - 无法追溯 AI 的决策过程

2. **缺少关键失败信息**
   - 看不到"security restriction error"
   - 看不到"captcha challenge"
   - 看不到"Verdict: Failure"
   - 只能看到最终的空结果

### 📍 对比示例

**之前的日志** (`logs/main/__main___20251007.log`):
```log
行79: ✅ AI爬取成功，执行了 6 步
行81: 📥 API RESPONSE: {"notes": []}
行83: ⚠️  AI返回数据格式异常或无数据
```
**看不出为什么失败！**

**改进后的日志** (`logs/browser_use/agent_20251007_010743.log` + `logs/main/__main___20251007.log`):
```log
📍 Step 1/2:
   ⚖️  评估: Starting agent with initial actions
   🎯 下一步目标: Execute initial navigation or setup actions
   🔗 当前页面: https://www.xiaohongshu.com

📍 Step 2/2:
   ⚖️  评估: The previous step was to navigate to the website,
            but a CAPTCHA is blocking access. Verdict: Failure
   🚫 检测到验证码挑战        ← 关键错误信息！
   ⚠️  步骤执行失败
   🎯 下一步目标: Report failure due to the CAPTCHA.
   🔗 当前页面: https://www.xiaohongshu.com/website-login/captcha...

📄 最终结果: {"notes": []}
```
**清晰地看到失败原因！**

---

## ✅ 实施的改进方案

### 1. 捕获 Browser-Use 库的日志

**修改位置**: `app/scrapers/browser_use_scraper.py:108-142`

```python
def _setup_browser_use_logging(self):
    """设置 browser-use 日志捕获到文件"""
    from datetime import datetime

    # 创建带时间戳的日志文件
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = BROWSER_USE_LOG_DIR / f"agent_{timestamp}.log"

    # 获取 browser-use 的根 logger
    browser_use_logger = logging.getLogger('browser_use')
    browser_use_logger.setLevel(logging.DEBUG)

    # 创建文件处理器
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)

    # 设置格式器
    formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)

    # 添加处理器
    if not any(isinstance(h, logging.FileHandler) for h in browser_use_logger.handlers):
        browser_use_logger.addHandler(file_handler)

    # 同时保留控制台输出
    if not browser_use_logger.handlers or not any(isinstance(h, logging.StreamHandler) for h in browser_use_logger.handlers):
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        browser_use_logger.addHandler(console_handler)

    logger.info(f"✓ Browser-Use 日志将输出到: {log_file}")
    self.browser_use_log_file = log_file
```

**效果**:
- ✅ Browser-Use 的所有日志自动写入 `logs/browser_use/agent_<timestamp>.log`
- ✅ 保留终端彩色输出
- ✅ 每次运行生成独立的日志文件

---

### 2. 详细记录 AI Agent 执行步骤

**修改位置**: `app/scrapers/browser_use_scraper.py:144-200`

```python
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

            # 记录下一步目标
            next_goal = getattr(model_output, 'next_goal', None)
            if next_goal:
                logger.info(f"   🎯 下一步目标: {next_goal}")

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
```

**效果**:
- ✅ 每一步的执行情况都写入应用日志
- ✅ 自动检测并高亮关键失败原因
- ✅ 记录 AI 的决策链路

---

### 3. 在 scrape_with_task() 中调用

**修改位置**: `app/scrapers/browser_use_scraper.py:271`

```python
# 详细记录每一步的执行情况
self._log_agent_steps(history)
```

**效果**:
- ✅ 每次 AI 执行后自动记录详细日志

---

## 📊 测试结果

### 测试命令
```bash
./run_xhs_scraper.sh "北京故宫" -n 2
```

### 生成的日志文件

#### 1. 应用日志 (`logs/main/__main___20251007.log`)

**包含**:
- ✅ 高层次的执行流程
- ✅ AI Agent 执行步骤详情
- ✅ 关键失败原因标记

**关键片段** (行320-324):
```log
2025-10-07 01:07:54 | INFO     | ... |    ⚖️  评估: The previous step was to navigate to the website, but a CAPTCHA is blocking access. Verdict: Failure
2025-10-07 01:07:54 | ERROR    | ... |    🚫 检测到验证码挑战
2025-10-07 01:07:54 | WARNING  | ... |    ⚠️  步骤执行失败
2025-10-07 01:07:54 | INFO     | ... |    🎯 下一步目标: Report failure due to the CAPTCHA.
2025-10-07 01:07:54 | INFO     | ... |    🔗 当前页面: https://www.xiaohongshu.com/website-login/captcha...
```

#### 2. Browser-Use 日志 (`logs/browser_use/agent_20251007_010743.log`)

**包含**:
- ✅ Browser-Use 内部的所有 DEBUG 日志
- ✅ LLM 调用详情
- ✅ 页面状态变化
- ✅ 元素交互记录

**关键片段**:
```log
2025-10-07 01:07:48 | INFO     | Agent | 📍 Step 1:
2025-10-07 01:07:48 | DEBUG    | browser_use.Agent | Evaluating page with 16 interactive elements on: https://www.xiaohongshu.com/website-login/captcha...
2025-10-07 01:07:54 | INFO     | Agent |   ⚠️ Eval: The previous step was to navigate to the website, but a CAPTCHA is blocking access. Verdict: Failure
2025-10-07 01:07:54 | DEBUG    | browser_use.Agent | 🧠 Memory: The website requires a CAPTCHA, which I cannot solve.
2025-10-07 01:07:54 | INFO     | Agent |   🎯 Next goal: Report failure due to the CAPTCHA.
```

---

## 🎯 改进效果总结

### Before (改进前)

```
❌ 只能看到：AI爬取成功，执行了 6 步，返回空数据
❓ 完全不知道为什么失败
🤷 需要手动运行命令查看终端输出
```

### After (改进后)

```
✅ 应用日志：完整的步骤详情 + 失败原因标记
✅ Browser-Use 日志：详细的内部执行过程
✅ 自动检测：安全限制/验证码/失败判定
✅ 决策链路：每一步的评估和下一步目标
```

---

## 📂 日志文件结构

```
logs/
├── main/
│   └── __main___20251007.log     # 应用日志（包含 AI 步骤详情）
└── browser_use/
    ├── agent_20251007_010615.log  # Browser-Use 详细日志（第1次运行）
    └── agent_20251007_010743.log  # Browser-Use 详细日志（第2次运行）
```

---

## 🔍 如何查看拦截证据

### 方法 1：查看应用日志中的关键标记

```bash
grep -E "🚫|⚠️" logs/main/__main___20251007.log
```

**输出**:
```
🚫 检测到验证码挑战
⚠️  步骤执行失败
```

### 方法 2：查看完整的执行步骤

```bash
grep -A 5 "📍 Step" logs/main/__main___20251007.log
```

**输出**:
```
📍 Step 1/2:
   ⚖️  评估: Starting agent with initial actions
   🎯 下一步目标: Execute initial navigation or setup actions

📍 Step 2/2:
   ⚖️  评估: ... CAPTCHA is blocking access. Verdict: Failure
   🚫 检测到验证码挑战
   ⚠️  步骤执行失败
```

### 方法 3：查看 Browser-Use 详细日志

```bash
grep -E "captcha|CAPTCHA|security|failure" logs/browser_use/agent_20251007_010743.log
```

**输出**:
```
website-login/captcha...
⚠️ Eval: The previous step was to navigate to the website, but a CAPTCHA is blocking access. Verdict: Failure
The website requires a CAPTCHA, which I cannot solve.
```

---

## 🎉 改进成果

| 指标 | 改进前 | 改进后 |
|------|--------|--------|
| **失败原因可见性** | ❌ 不可见 | ✅ 清晰标记 |
| **Browser-Use 日志** | ❌ 仅终端 | ✅ 文件持久化 |
| **AI 决策链路** | ❌ 缺失 | ✅ 完整记录 |
| **关键错误检测** | ❌ 无 | ✅ 自动高亮 |
| **日志文件数量** | 1 个 | 2 个（分层清晰） |
| **调试友好度** | ⭐⭐☆☆☆ | ⭐⭐⭐⭐⭐ |

---

## 📝 后续建议

### 1. 添加日志清理策略

```python
# app/utils/log_cleaner.py
def clean_old_logs(days=7):
    """删除 N 天前的日志文件"""
    cutoff = datetime.now() - timedelta(days=days)
    for log_file in Path("logs/browser_use").glob("*.log"):
        if log_file.stat().st_mtime < cutoff.timestamp():
            log_file.unlink()
```

### 2. 添加日志搜索工具

```python
# app/utils/log_search.py
def search_failures(log_dir="logs/browser_use"):
    """搜索所有包含失败原因的日志"""
    failures = []
    for log_file in Path(log_dir).glob("*.log"):
        with open(log_file) as f:
            content = f.read()
            if "Verdict: Failure" in content:
                failures.append(log_file)
    return failures
```

### 3. 集成到 Web 界面

在 Streamlit 界面中添加：
- 📊 实时日志查看器
- 🔍 失败原因搜索
- 📥 日志下载按钮

---

## 🔗 相关文档

- [日志分析文档](./debug_log_analysis.md)
- [测试报告](../tests/test_report_20251007.md)
- [CLAUDE.md - 程序启动流程](../CLAUDE.md#程序启动流程详解)

---

**状态**: ✅ 已完成并测试通过
**维护者**: Browser-Brain Team
**最后更新**: 2025-10-07
