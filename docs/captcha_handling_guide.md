# 验证码处理指南

**版本**: v1.4
**更新时间**: 2025-10-07
**功能**: 小红书爬虫验证码人工处理机制

---

## 📋 功能概述

为了应对小红书的反爬虫验证码拦截,系统已实现**验证码人工处理机制**:

- ✅ 自动检测验证码页面
- ✅ 暂停60秒等待人工完成验证
- ✅ 实时显示剩余等待时间
- ✅ 自动重新尝试爬取任务

---

## 🔧 工作原理

### 1. 验证码检测

系统在AI爬取完成后检查访问的URL列表:

```python
# app/scrapers/xhs_scraper.py:107-122
if result["status"] == "success" and result.get("urls"):
    visited_urls = result["urls"]
    # 检查是否访问了验证码页面
    if any("captcha" in url.lower() for url in visited_urls):
        logger.warning("🚫 检测到访问了验证码页面，启动人工处理流程...")

        # 暂停等待人工处理
        await self._handle_captcha_manual(wait_seconds=60)

        # 重新尝试执行任务
        result = await self.scrape_with_task(...)
```

**检测依据**: URL中包含关键词"captcha"

**示例URL**:
```
https://www.xiaohongshu.com/website-login/captcha?redirectPath=...
```

---

### 2. 人工验证流程

**核心函数**: `_handle_captcha_manual()` (app/scrapers/xhs_scraper.py:35-51)

```python
async def _handle_captcha_manual(self, wait_seconds: int = 60):
    """验证码人工处理：暂停等待用户手动完成验证"""
    logger.warning("⚠️  检测到验证码，暂停等待人工处理...")
    logger.info("📌 请在浏览器窗口中完成验证码验证")
    logger.info(f"⏳ 系统将在 {wait_seconds} 秒后自动继续...")

    # 每10秒提示一次剩余时间
    for remaining in range(wait_seconds, 0, -10):
        logger.info(f"⏱️  剩余等待时间: {remaining} 秒")
        await asyncio.sleep(min(10, remaining))

    logger.info("✅ 等待结束，继续执行任务...")
```

**执行步骤**:
1. 输出警告信息，提示用户完成验证
2. 每10秒输出一次剩余时间(60秒 → 50秒 → ... → 10秒)
3. 等待结束后返回，继续执行

---

### 3. 自动重试机制

等待结束后,系统会自动重新尝试爬取任务:

```python
# 重新尝试执行任务
logger.info("🔄 重新尝试执行爬取任务...")
result = await self.scrape_with_task(
    task=task,
    output_model=XHSNotesCollection,
    max_steps=30
)
```

**预期效果**:
- 如果用户在60秒内完成验证 → 重试成功,继续爬取
- 如果未完成验证 → 重试可能再次遇到验证码

---

## 🎮 使用指南

### 运行爬虫（有头模式）

```bash
# 运行小红书爬虫（会显示浏览器窗口）
.venv/bin/python app/scrapers/run_xhs.py "北京故宫" -n 2

# 或使用脚本
./run_xhs_scraper.sh "北京故宫" -n 2
```

**重要**: 必须使用**有头模式**（默认配置），否则看不到验证码页面。

---

### 日志输出示例

**正常流程（遇到验证码）**:

```
[INFO] 🔗 当前页面: https://www.xiaohongshu.com
[INFO] ⚖️  评估: The previous step navigated to the website but landed on a captcha page
[INFO] ✅ AI爬取成功，执行了 2 步
[WARNING] 🚫 检测到访问了验证码页面，启动人工处理流程...

[WARNING] ⚠️  检测到验证码，暂停等待人工处理...
[INFO] 📌 请在浏览器窗口中完成验证码验证
[INFO] ⏳ 系统将在 60 秒后自动继续...
[INFO] ⏱️  剩余等待时间: 60 秒
[INFO] ⏱️  剩余等待时间: 50 秒
[INFO] ⏱️  剩余等待时间: 40 秒
[INFO] ⏱️  剩余等待时间: 30 秒
[INFO] ⏱️  剩余等待时间: 20 秒
[INFO] ⏱️  剩余等待时间: 10 秒
[INFO] ✅ 等待结束，继续执行任务...

[INFO] 🔄 重新尝试执行爬取任务...
[INFO] AI开始控制浏览器...
```

---

### 用户操作步骤

1. **观察日志** - 看到"检测到验证码"提示时
2. **切换到浏览器窗口** - 找到自动打开的Chrome窗口
3. **完成验证码** - 点击、拖动、选择等操作
4. **等待系统继续** - 无需手动操作，系统会自动重试

**注意事项**:
- ✅ 验证码完成后不要关闭浏览器
- ✅ 不要手动刷新页面
- ✅ 保持在当前页面，等待系统自动继续

---

## 🔍 技术细节

### 配置参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `wait_seconds` | 60 | 等待时间（秒） |
| 提醒间隔 | 10秒 | 每10秒输出一次剩余时间 |
| 最大重试次数 | 1次 | 当前只重试1次 |

**修改等待时间**:

```python
# app/scrapers/xhs_scraper.py:114
await self._handle_captcha_manual(wait_seconds=120)  # 改为120秒
```

---

### 检测逻辑

**检测代码** (app/scrapers/xhs_scraper.py:107-110):
```python
if result["status"] == "success" and result.get("urls"):
    visited_urls = result["urls"]
    if any("captcha" in url.lower() for url in visited_urls):
        # 触发人工处理流程
```

**检测规则**:
- ✅ AI爬取状态为"success"
- ✅ 存在访问的URL列表
- ✅ 任意URL包含"captcha"关键词（不区分大小写）

**可能的验证码URL**:
```
https://www.xiaohongshu.com/website-login/captcha?...
https://www.xiaohongshu.com/verify/captcha?...
```

---

## ⚠️ 已知限制

### 1. 固定等待时间

**问题**: 等待时间固定为60秒
- 简单验证码可能10秒就完成 → 浪费50秒
- 复杂验证码可能需要90秒 → 时间不够

**改进建议**:
```python
# 动态调整等待时间
if is_complex_captcha():
    wait_seconds = 120
else:
    wait_seconds = 60
```

---

### 2. 仅重试1次

**问题**: 如果第1次重试仍遇到验证码，直接失败

**改进建议**:
```python
max_retry = 3
for attempt in range(max_retry):
    result = await self.scrape_with_task(...)
    if not has_captcha(result):
        break
    await self._handle_captcha_manual()
```

---

### 3. 无法检测非URL跳转的验证码

**问题**: 有些验证码是弹窗形式，URL不变

**改进建议**:
- 检测页面标题是否包含"验证"
- 检测页面是否包含验证码元素
- 使用AI视觉能力识别验证码页面

---

## 📚 相关文档

- 修复总结: `docs/fix_summary_20251007.md`
- 验证测试报告: `docs/validation_test_report_20251007.md`
- 项目文档: `CLAUDE.md`

---

## 🎯 下一步优化

### P1 - Cookie登录功能

**目的**: 减少验证码触发频率

**实现**:
- 第一次人工登录并保存Cookie
- 后续运行自动加载Cookie
- 登录状态下验证码大幅减少

**预期效果**:
- ✅ 第一次: 人工登录 + 保存Cookie
- ✅ 后续: 自动加载 + 绕过验证码

---

### P2 - 智能重试策略

**改进点**:
- 动态调整等待时间（根据验证码复杂度）
- 多次重试（最多3次）
- 指数退避（第1次等60秒，第2次等120秒，第3次等240秒）

---

**文档版本**: v1.4
**维护者**: Browser-Brain Team
**最后更新**: 2025-10-07 10:55
