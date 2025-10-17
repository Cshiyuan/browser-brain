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
- 🛡️ 增强反检测配置（隐藏自动化标识、真实 User-Agent）
- 🔐 验证码人工处理机制（自动检测并暂停等待）
- ⚡ Fast Mode 速度优化（可选）
- 🪟 智能窗口布局（多窗口并发时自动平铺）


### 启动应用

```bash
# Web 界面（推荐）
./run_web.sh
```

**⚠️ 重要提示**：
- 默认使用有头浏览器模式（显示浏览器窗口）
- 便于观察 AI 操作过程和发现反爬虫问题
- 在 `.env` 文件中配置：`HEADLESS=false`
- 所有爬虫通过 Web 界面或 PlannerAgent 调用,无需独立运行

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
│   │   └──xhs_scraper.py         # 小红书爬虫
│   ├── models/
│   │   ├── prompts.py             # AI 提示词统一管理
│   │   ├── attraction.py          # 景点数据模型（业务模型）
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


## ⚙️ 配置说明

### 环境变量（.env）

```bash
# LLM 配置
LLM_PROVIDER=google             # openai/anthropic/google
LLM_MODEL=gemini-2.5-flash
GOOGLE_API_KEY=AIza...

# 爬虫配置
HEADLESS=false                  # 有头浏览器模式（默认）
XHS_MAX_NOTES=5
MAX_SCRAPE_TIMEOUT=300

# Web 界面
STREAMLIT_SERVER_PORT=8501
```

### 数据目录结构

```
data/
├── browser/                       # 浏览器数据
│   ├── storage_state.json        # 持久化 cookies（保留登录状态）
│   └── tmp_user_data_*/              # 临时用户数据目录（会话级，自动生成）
├── cache/                         # 缓存数据
├── db/                            # 数据库文件
└── plans/                         # 旅行方案
```

**说明**：
- `storage_state.json`：保存登录 cookies，避免重复登录
- `tmp_user_data_*`：每次运行自动生成随机临时目录，包含完整浏览器状态
- 清理临时目录：运行 `./scripts/cleanup_browser_data.sh`

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
- 通过 Web 界面验证功能
- 依赖 Pylint 和 Mypy 做静态检查

---


## 📋 代码参考索引

**核心文件位置**:
- 前端入口: `frontend/app.py`
- 后端核心: `app/agents/planner_agent.py`
- AI 爬虫基类: `app/scrapers/browser_use_scraper.py`
- 小红书爬虫: `app/scrapers/xhs_scraper.py`
- 提示词模型: `app/models/prompts.py`
- 数据模型: `app/models/attraction.py`

---

**最后更新**: 2025-10-12
**维护者**: Browser-Brain Team
**版本**: v1.6.0
- 将欧卡姆剃刀定律作为修改代码的准则