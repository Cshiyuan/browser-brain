# Browser-Brain 项目文档

> 基于 Browser-Use AI 的智能旅行规划系统

## 🎯 项目概述

Browser-Brain 是一个使用 AI 驱动的旅行规划应用，通过自然语言控制浏览器自动爬取小红书和景点官网信息，生成个性化旅行方案。

**核心特性**:
- 🤖 Browser-Use AI 框架驱动的智能网页爬取
- 🌐 Streamlit Web 界面
- 📊 灵活的上下文数据模型设计
- 🔄 异步并发爬取
- 🎨 支持多种 LLM（OpenAI/Claude/Gemini）
- 🚀 独立收集器模式（可单独运行）
- 🛡️ 增强反检测配置（隐藏自动化标识、真实 User-Agent）
- 🔐 验证码人工处理机制（自动检测并暂停等待）
- ⚡ Fast Mode 速度优化（可选）
- 🔗 Chain Agent Tasks（任务链式执行，保持浏览器会话）


### 启动应用

```bash
# 方式一：Web 界面（推荐）
./run_web.sh

# 方式二：独立收集器（默认有头模式）
./run_xhs_scraper.sh "北京故宫" -n 5
./run_official_scraper.sh "北京故宫" -l "https://www.dpm.org.cn"
```

**⚠️ 重要提示**：
- 默认使用有头浏览器模式（显示浏览器窗口）
- 便于观察 AI 操作过程和发现反爬虫问题
- 在 `.env` 文件中配置：`HEADLESS=false`

### 代码检查

```bash
# Pylint（代码质量检查）
.venv/bin/pylint app/ --disable=C,R --errors-only --recursive=y

# Mypy（类型检查）
./check_types.sh
```

### 日志配置

项目使用统一的日志系统（基于 loguru），支持环境变量配置。

```bash
# 默认 INFO 级别
./run_web.sh

# DEBUG 级别（显示详细日志）
LOG_LEVEL=DEBUG ./run_web.sh

# 生产环境（只显示警告和错误）
LOG_LEVEL=WARNING ./run_web.sh
```

**日志文件结构**（统一目录存储，文件名前缀区分模块）：

```
logs/
├── scrapers_xhs_scraper_20251009.log
├── scrapers_official_scraper_20251009.log
├── agents_planner_agent_20251009.log
├── frontend_app_20251009.log
└── browser_use_agent_20251009_143022.log
```

**快速查找日志**：
```bash
# 查看爬虫相关日志
ls -lh logs/scrapers_*

# 查看特定模块日志
tail -f logs/scrapers_xhs_scraper_20251009.log

# 搜索错误日志
grep -r "ERROR" logs/
```

## 🏗️ 架构设计

### 核心组件

```
browser-brain/
├── app/
│   ├── agents/
│   │   └── planner_agent.py      # 旅行规划 Agent
│   ├── scrapers/
│   │   ├── models.py              # 爬虫数据模型（AI 返回结构）
│   │   ├── browser_use_scraper.py # AI 爬虫基类
│   │   ├── xhs_scraper.py         # 小红书爬虫
│   │   ├── official_scraper.py    # 官网爬虫
│   │   ├── run_xhs.py             # 小红书独立运行脚本
│   │   └── run_official.py        # 官网独立运行脚本
│   ├── models/
│   │   ├── prompts.py             # AI 提示词统一管理
│   │   ├── attraction.py          # 景点数据模型（业务模型）
│   │   └── trip_plan.py           # 旅行方案模型
│   └── utils/
│       └── logger.py              # 日志工具
├── frontend/
│   └── app.py                     # Streamlit Web 界面
└── config/
    └── settings.py                # 配置管理
```

**模型分层说明**：
- `app/scrapers/models.py`: Browser-Use AI 返回的数据结构
- `app/models/`: 业务层数据模型
- `app/models/prompts.py`: AI 任务提示词模型

### 前后端通信架构

Streamlit 单体架构：前后端运行在同一进程，通过直接函数调用通信。

**数据流**：
```
用户输入 → Streamlit UI → PlannerAgent
                ↓
          并发启动 AI 爬虫
          ├── XHSScraper（小红书）
          └── OfficialScraper（官网）
                ↓
          收集景点信息 → Attraction 对象
                ↓
          生成行程方案 → TripPlan 对象
                ↓
          格式化输出 → 显示给用户
```

## 🔑 关键设计模式

### 1. 独立收集器模式

每个收集器可以独立运行，支持命令行参数和 JSON 输出。

**小红书收集器**：
```bash
./run_xhs_scraper.sh "北京故宫" -n 5
```

**官网收集器**：
```bash
./run_official_scraper.sh "北京故宫" -l "https://www.dpm.org.cn"
```

### 2. 上下文数据模型

`TripPlan` 和 `Attraction` 使用灵活的上下文字典而非固定属性。

```python
# ✅ 正确：使用 get() 方法
itinerary_data = plan.get("ai_planning.itinerary", {})
highlights = plan.get("ai_planning.highlights", [])

# ❌ 错误：直接访问属性
plan.daily_itineraries  # AttributeError!
```

### 3. 爬虫数据模型统一管理

所有爬虫使用的 Pydantic 模型统一定义在 `app/scrapers/models.py` 中。

**模型分层架构**：
```
app/scrapers/models.py (爬虫数据模型)
  - XHSNoteOutput
  - XHSNotesCollection
  - OfficialInfoOutput
  ↓ 转换
app/models/ (业务数据模型)
  - XHSNote
  - Attraction
  - TripPlan
```

### 4. AI 提示词统一管理

所有 AI 任务提示词统一定义在 `app/models/prompts.py` 中。

```python
from app.models.prompts import XHSPrompts, OfficialPrompts, SystemPrompts

# 生成小红书搜索任务提示词
task = XHSPrompts.search_attraction_task("北京故宫", max_notes=5)

# 生成官网信息提取任务提示词
task = OfficialPrompts.get_official_info_without_links_task("北京故宫")

# 使用系统速度优化提示词
agent = Agent(extend_system_message=SystemPrompts.SPEED_OPTIMIZATION)
```

**提示词模型定义**：
```python
class SystemPrompts:
    """系统级提示词"""
    SPEED_OPTIMIZATION = "..."

class XHSPrompts:
    """小红书爬虫提示词"""
    @staticmethod
    def search_attraction_task(attraction_name: str, max_notes: int) -> str:
        return f"任务：在小红书搜索"{attraction_name}"..."

class OfficialPrompts:
    """官网爬虫提示词"""
    @staticmethod
    def get_official_info_with_links_task(...) -> str:
        return "..."
```

### 5. Browser-Use AI 集成

所有爬虫继承自 `BrowserUseScraper` 基类：

```python
class XHSScraper(BrowserUseScraper):
    async def scrape(self, attraction_name: str, max_notes: int):
        # 使用提示词模型生成任务
        task = XHSPrompts.search_attraction_task(attraction_name, max_notes)

        # AI 执行任务
        result = await self.scrape_with_task(
            task=task,
            output_model=XHSNotesCollection,
            max_steps=30
        )
        return self._parse_result(result)
```

**核心方法** (`app/scrapers/browser_use_scraper.py`):
```python
async def scrape_with_task(
    self,
    task: str,                                      # 任务描述
    output_model: Optional[type[BaseModel]] = None, # Pydantic模型
    max_steps: int = 20,                            # 最大步骤数
    use_vision: bool = True                         # 是否使用视觉能力
) -> dict
```

### 6. Pydantic 数据验证

所有模型字段必须类型匹配：

```python
# ✅ 正确：类型转换
DailyItinerary(
    date=str(datetime.date(2025, 10, 4)),
    notes="\n".join(["提示1", "提示2"])
)

XHSNote(created_at=datetime.now().isoformat())

# ❌ 错误：类型不匹配
DailyItinerary(
    date=datetime.date(2025, 10, 4),  # 期望 str
    notes=["提示1", "提示2"]           # 期望 str
)
```

### 7. 异步并发

使用 `asyncio.gather()` 实现并发爬取：

```python
# 并发爬取多个景点
tasks = [
    self._scrape_single_attraction_ai(dest, attr, xhs, official)
    for attr in must_visit
]
results = await asyncio.gather(*tasks, return_exceptions=True)
```

## ⚙️ 配置说明

### 环境变量（.env）

```bash
# LLM 配置
LLM_PROVIDER=google             # openai/anthropic/google
LLM_MODEL=gemini-2.0-flash-exp
GOOGLE_API_KEY=AIza...

# 爬虫配置
HEADLESS=false                  # 有头浏览器模式（默认）
XHS_MAX_NOTES=5
MAX_SCRAPE_TIMEOUT=300

# Web 界面
STREAMLIT_SERVER_PORT=8501
```

### Pylint 配置

- 禁用过于严格的检查（C0103, C0114, C0115, C0116, R0903, R0913）
- 允许短变量名：`i, j, k, ex, _, id, db, st`
- 最大行长度：120

## 🔬 核心开发原则

### 📝 文档编写规则

**重要原则 1**：不要在每次操作后自动创建独立的 README 或文档文件

**原因**：
- 避免文档碎片化和维护困难
- CLAUDE.md 是项目的单一信息源

**例外情况**（用户明确要求时才创建）：
- API 文档（如 `docs/api.md`）
- 部署文档（如 `docs/deployment.md`）

---

**重要原则 2**：不要频繁大量修改 CLAUDE.md

**原因**：
- CLAUDE.md 是项目文档，不是每次修改的日志
- 大量修改会导致文档臃肿、难以维护
- 文档应该保持**简洁、核心、稳定**

**何时才能修改 CLAUDE.md**：
- ✅ 架构重大变更（如新增核心模块）
- ✅ 核心设计原则变更（如 KISS 原则、重构策略）
- ✅ 用户明确要求更新文档
- ❌ 日常代码修改（如修复 bug、优化细节）
- ❌ 新增单个功能（除非是核心功能）

**修改时遵循原则**：
1. **简洁优先**：只保留核心要点，删除冗余说明
2. **删除比新增更有价值**
3. **避免大量示例代码**

---

### 🎨 KISS 原则（Keep It Simple, Stupid）

**核心理念**：简单即美，过度设计是万恶之源

KISS 原则强调：
- 保持代码和架构的**简单性**
- 避免**不必要的复杂性**
- 优先选择**最直接的解决方案**
- **删除比新增更有价值**

> 💡 "Perfection is achieved, not when there is nothing more to add, but when there is nothing left to take away."
> — Antoine de Saint-Exupéry

**判断是否违反 KISS 原则**：

⚠️ **警告信号**：
- 新人需要超过 1 天才能理解某个模块
- 修改一个功能需要改动 5 个以上的文件
- 代码中有超过 3 层的抽象
- 需要写很长的文档才能解释清楚
- "我们以后可能需要..."（YAGNI）

✅ **健康信号**：
- 代码功能一目了然
- 删除代码比新增代码更频繁
- 新功能可以快速添加
- 文档简洁清晰

**实践口诀**：
- **能删不留**（代码越少越好）
- **能简不繁**（逻辑越清晰越好）
- **能直不绕**（路径越短越好）
- **能统不散**（集中管理优于分散配置）

---

### ⚠️ 问题调试的正确方法

**重要原则**: 遇到问题时，**必须深入分析问题根源**，而不是绕过问题使用替代方案。

**正确的问题处理流程**：
```
1. 🔍 发现问题
2. 📊 收集现象和日志
3. 🧠 分析问题根本原因
4. 🔬 逐层深入验证假设
5. ✅ 找到真正的问题所在
6. 🔧 修复根本问题
7. ✓ 验证修复效果
```

**牢记这条原则**：
> 🎯 不要绕过问题，要解决问题的根本原因。
> 临时方案会积累技术债务，只有彻底解决问题才能保证系统稳定性。

---

### 🧪 测试原则

**重要原则**: 不要主动创建单元测试文件或测试脚本

**原因**：
- 测试增加维护成本
- 本项目基于 AI 爬虫，测试难度大（依赖外部网站）
- 手动测试更直观高效

**何时才创建测试**：
- ✅ 用户明确要求时
- ❌ 完成功能后自动创建测试
- ❌ "为了测试覆盖率"而创建测试

**替代方案**：
- 使用独立收集器脚本手动测试
- 通过 Web 界面验证功能
- 依赖 Pylint 和 Mypy 做静态检查

---

## ⚡ Fast Mode 速度优化策略

基于 Browser-Use 官方 Fast Agent 模板优化爬虫性能。

### 核心优化技术

**1. Flash Mode（LLM 优化）**

禁用 LLM 的"thinking"过程，直接输出决策：
```python
agent = Agent(
    task=task,
    llm=llm,
    flash_mode=True,  # 关键优化
    ...
)
```

**效果**：LLM响应速度提升 2-3倍

**2. 速度优化提示词**

```python
from app.models.prompts import SystemPrompts

agent = Agent(extend_system_message=SystemPrompts.SPEED_OPTIMIZATION)
```

**3. 浏览器配置优化**

| 参数 | 标准模式 | Fast Mode |
|------|----------|-----------|
| `wait_for_network_idle_page_load_time` | 2.0s | 0.1s |
| `maximum_wait_page_load_time` | 10.0s | 5.0s |
| `wait_between_actions` | 1.0s | 0.1s |

### 组合使用

```python
scraper = XHSScraper(
    headless=True,
    fast_mode=True     # 最大化速度
)
# 预期效果: 2-3倍加速
```


## 🎓 架构决策记录

### 为什么使用上下文数据模型？

**优势**:
- ✅ 灵活存储任意结构数据
- ✅ AI 可自由填充内容
- ✅ 扩展性强，无需修改代码

### 为什么使用 Browser-Use？

**相比传统爬虫**:
- ✅ AI 自动处理页面变化
- ✅ 自然语言描述任务
- ✅ 无需维护选择器
- ✅ 支持结构化输出

### 为什么选择 Streamlit？

**优势**:
- ✅ 快速构建 Web UI
- ✅ Python 原生，无需前后端分离
- ✅ 适合 AI 应用原型

**局限性**:
- ❌ 耦合度高，难以独立扩展
- ❌ 单点故障

### 为什么设计独立收集器？

**动机**:
- 便于调试和测试
- 支持命令行批量处理
- 可以集成到其他系统
- 解耦数据收集和业务逻辑

---

## 📚 相关资源

- [Browser-Use 文档](https://github.com/browser-use/browser-use)
- [Streamlit 文档](https://docs.streamlit.io)
- [Pydantic 文档](https://docs.pydantic.dev)

## 📋 代码参考索引

**核心文件位置**:
- 前端入口: `frontend/app.py`
- 后端核心: `app/agents/planner_agent.py`
- AI 爬虫基类: `app/scrapers/browser_use_scraper.py`
- 小红书爬虫: `app/scrapers/xhs_scraper.py`
- 官网爬虫: `app/scrapers/official_scraper.py`
- 提示词模型: `app/models/prompts.py`
- 数据模型: `app/models/attraction.py`

---

**最后更新**: 2025-10-12
**维护者**: Browser-Brain Team
**版本**: v1.6.0
