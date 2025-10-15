# 🤖 AI智能旅行规划助手

基于Browser-Use AI Agent的全自动旅行规划系统,完全由AI驱动爬取小红书、官网信息并生成个性化旅行方案。

---

## 🎯 快速开始

### 一键启动 (推荐)

```bash
# 1. 配置API Key
cp .env.example .env
nano .env  # 填入你的API Key

# 2. 启动Web界面
bash run_web.sh
```

访问 `http://localhost:8501` 开始使用!

---

## ✨ 核心特性

### 🎯 AI驱动
- ✅ **AI自主浏览网页**: 使用Browser-Use让AI像人类一样浏览网站
- ✅ **智能信息提取**: AI自动识别并提取关键信息
- ✅ **自适应爬取**: AI根据页面结构自动调整策略
- ✅ **无需维护选择器**: 不再需要更新CSS/XPath选择器

### 🔧 技术栈

```
AI Agent (GPT-4/Claude)
    ↓
Browser-Use Framework
    ↓
自动化浏览器控制
    ↓
智能数据提取
```

## 🚀 快速开始

### 1. 环境准备

```bash
# Python 3.11+
python --version

# 克隆项目
git clone <your-repo>
cd ai-travel-planner
```

### 2. 安装依赖

```bash
# 安装Python依赖(包含browser-use)
pip install -r requirements.txt

# 安装Playwright浏览器
playwright install chromium
```

### 3. 配置API Key

创建 `.env` 文件:

```bash
# 🎯 推荐：使用Google Gemini（快速+免费额度）
GOOGLE_API_KEY=your-google-api-key-here
LLM_PROVIDER=google
LLM_MODEL=gemini-2.5-flash

# 浏览器配置
HEADLESS=false  # 显示浏览器窗口，方便观察AI操作
XHS_MAX_NOTES=5
MAX_SCRAPE_TIMEOUT=300
```

**获取API Key:**
- 🌟 **Google Gemini** (推荐): [https://makersuite.google.com/app/apikey](https://makersuite.google.com/app/apikey)
  - ✅ 免费额度充足
  - ✅ 速度快
  - ✅ 支持视觉理解
- OpenAI: [https://platform.openai.com/api-keys](https://platform.openai.com/api-keys)
- Anthropic: [https://console.anthropic.com/](https://console.anthropic.com/)

### 4. 启动应用

**🌐 Web界面（推荐）**

```bash
bash run_web.sh
```

访问 `http://localhost:8501` 开始使用

## 📖 AI工作流程详解

### 阶段1: AI搜索小红书

```
用户输入"故宫" → AI Agent执行:
  1. 访问小红书网站
  2. 搜索"故宫"
  3. 浏览搜索结果
  4. 点击热门笔记
  5. 提取标题、内容、点赞数
  6. 识别官网链接和关键词
  7. 收集图片URL
  8. 返回结构化JSON数据
```

**AI自动处理:**
- ✅ 页面加载等待
- ✅ 登录弹窗处理
- ✅ 动态内容滚动
- ✅ 数据格式化
- ✅ 错误重试

### 阶段2: AI访问官网

```
从小红书获取可能的官网链接 → AI Agent执行:
  1. 验证链接真实性
  2. 如果无效,使用百度/Google搜索
  3. 识别真正的官方网站
  4. 访问官网
  5. 提取开放时间、门票价格
  6. 获取预订方式、联系信息
  7. 返回结构化JSON数据
```

**AI智能识别:**
- ✅ 官方网站 vs 第三方平台
- ✅ .gov.cn政府域名优先
- ✅ 跳过广告和无关链接
- ✅ 处理复杂页面结构

### 阶段3: AI生成方案

- 分析景点热度和推荐指数
- 智能分配每日行程
- 估算旅行预算
- 提取亮点和贴士

## 🎯 技术亮点

### 1. Browser-Use AI Agent

```python
# 传统方式: 手动编写
await page.goto("https://xiaohongshu.com")
await page.fill(".search-input", "故宫")
await page.click(".search-button")
await page.wait_for_selector(".note-item")
# ... 100+ 行代码

# Browser-Use AI方式: 自然语言
task = "在小红书搜索故宫,找到前5篇笔记并提取信息"
result = await agent.run(task)
```

### 2. 结构化输出

```python
class XHSNoteOutput(BaseModel):
    title: str
    author: str
    content: str
    likes: int
    extracted_links: List[str]
    keywords: List[str]

# AI自动填充结构化数据
notes = await agent.run(
    task="搜索小红书故宫笔记",
    output_model=XHSNoteOutput
)
```

### 3. 智能链接发现

```python
# AI自动:
# 1. 从小红书笔记提取官网链接
# 2. 验证链接有效性
# 3. 如果无效,使用搜索引擎
# 4. 智能识别真正的官网
# 5. 提取完整信息

官网信息 = await ai_agent.get_official_info("故宫")
```

## ⚙️ 配置选项

### LLM模型选择

```bash
# 推荐配置(速度快+成本低)
LLM_PROVIDER=openai
LLM_MODEL=gpt-4.1-mini

# 高精度配置
LLM_PROVIDER=openai
LLM_MODEL=gpt-4.1

# Anthropic Claude
LLM_PROVIDER=anthropic
LLM_MODEL=claude-3-sonnet-20240229
```


## 🏗️ 技术架构

```
├── app/
│   ├── agents/              # AI Agent层
│   │   └── planner_agent.py      # 总协调Agent
│   ├── scrapers/            # AI爬虫层
│   │   ├── browser_use_scraper.py # AI爬虫基类
│   │   ├── xhs_scraper.py         # 小红书AI爬虫
│   │   └── official_scraper.py    # 官网AI爬虫
│   ├── models/              # 数据模型
│   │   ├── attraction.py         # 景点模型
│   │   └── trip_plan.py         # 旅行方案模型
│   └── utils/               # 工具函数
│       └── logger.py            # 日志工具
├── frontend/
│   └── app.py              # Streamlit Web界面
├── config/
│   └── settings.py         # 配置管理
└── data/                   # 数据存储
```

## 🚧 待实现功能

**Phase 2 - 完善数据源**
- [ ] 携程酒店AI爬虫
- [ ] 携程机票AI爬虫
- [ ] 美团/大众点评餐饮AI爬虫

**Phase 3 - 智能优化**
- [ ] 多方案生成与对比
- [ ] 个性化推荐算法
- [ ] 实时价格监控

**Phase 4 - 产品化**
- [ ] FastAPI后端
- [ ] 用户账号系统
- [ ] 方案分享功能

## ⚠️ 注意事项

### API成本
- OpenAI GPT-4.1-mini: 性价比最高
- 设置`MAX_SCRAPE_TIMEOUT`限制单次爬取时间
- 调整`XHS_MAX_NOTES`控制数据量

### 网站反爬
- Browser-Use模拟真实浏览行为
- 比传统爬虫更难被检测
- 建议使用Browser-Use Cloud以获得更好的成功率

### 法律合规
- ⚠️ 仅供学习和个人研究
- ⚠️ 遵守网站robots.txt
- ⚠️ 不得用于商业用途

## 🔧 调试技巧

### 查看AI执行过程

```bash
# Web界面：在侧边栏取消勾选"无头模式"
# 浏览器窗口会显示，可以观察AI的操作过程
```

### 查看日志

```bash
# 开启DEBUG日志
export LOG_LEVEL=DEBUG
bash run_web.sh

# 查看日志文件
tail -f logs/scrapers_xhs_scraper_$(date +%Y%m%d).log
```

## 🙏 致谢

- **Browser-Use**: [https://github.com/browser-use/browser-use](https://github.com/browser-use/browser-use)
- **OpenAI GPT-4**: 强大的AI能力
- **Anthropic Claude**: 高质量的推理能力
- **Playwright**: 可靠的浏览器自动化

## 📝 许可证

MIT License

---

**创建时间**: 2025-01
**最后更新**: 2025-01-03
