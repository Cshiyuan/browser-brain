"""AI爬虫提示词模型 - 统一管理所有任务提示词"""


class SystemPrompts:
    """系统级提示词"""

    # Fast Agent速度优化提示词
    SPEED_OPTIMIZATION = """
Speed optimization instructions:
- Be extremely concise and direct in your responses
- Get to the goal as quickly as possible
- Use multi-action sequences whenever possible to reduce steps
- Minimize thinking time and focus on action execution
- Always reference actions by their exact names (e.g., "use click action", "use extract action")
- If an action fails, immediately try keyboard navigation as backup
"""


class XHSPrompts:
    """小红书爬虫提示词"""

    @staticmethod
    def search_destination_guide_task(destination: str, max_attractions: int) -> str:
        """生成搜索目的地攻略任务提示词"""
        return f"""
    任务：在小红书搜索"{destination}旅游攻略"，提取推荐景点列表（目标：{max_attractions}个景点）

    具体步骤：
    1. 使用 go_to_url 操作访问: https://www.xiaohongshu.com/search_result?keyword={destination}旅游攻略
    2. 使用 wait 操作等待 2-3 秒确保页面加载
    3. 识别相关性更高的笔记，依次选择（笔记不够时，则向下滑动查找）
    4. 针对每篇笔记：
       a. 使用 click 操作打开笔记
       b. 使用 extract 操作提取景点信息：
          - 景点名称（明确的景点名）
          - 推荐理由（为什么推荐）
          - 优先级判断（"必去"=5，"推荐"=4，"可选"=3）
          - 额外信息（需要注意的事项，比如地理位置、相邻景点，开放时间，打卡点，游玩项目）
       c. 使用 Sent keys: Escape 操作关闭笔记
       d. 继续处理，直到收集至少 {max_attractions} 个景点

    错误处理：
    - 如果 click 操作失败：使用 send_keys 操作输入 "Tab Enter" 进行导航
    - 如果单个笔记数据不足：使用 go_back 操作返回并尝试下一篇（至少尝试 3 篇）
    - 如果页面超时：使用 refresh 操作刷新页面，然后使用 wait 操作等待 10 秒
    - 始终在 msg 字段中包含成功/失败状态及简要描述

    登录/验证码处理：
    - 遇到登录要求：停留在登录页面，在 JSON 中返回 status="login"
    - 遇到验证码：停留在验证码页面，在 JSON 中返回 status="captcha"
    - 正常完成：在 JSON 中返回 status="success"

    输出要求：
    - 使用 extract 操作输出结构化 JSON 格式
    - 包含 msg 字段，简要说明执行情况
    """


    @staticmethod
    def search_attraction_task(attraction_name: str, max_notes: int) -> str:
        """生成搜索景点任务提示词"""
        return f"""
任务：在小红书搜索"{attraction_name}"相关的旅游笔记，提取{max_notes}条实用的景点知识点

⚠️ 重要：不要返回完整笔记，只提取对游客有用的关键信息！

具体步骤：
1. 使用 go_to_url 操作访问: https://www.xiaohongshu.com/search_result?keyword={attraction_name}攻略
2. 使用 wait 操作等待 2-3 秒确保页面加载
3. 识别相关性更高的笔记，依次打开并提取知识点：
   a. 使用 click 操作打开笔记
   b. 使用 extract  操作从笔记正文和评论中提取**实用知识点**：

      📋 提取目标（每条知识点）：
      - attraction_name: 景点名称（就是 "{attraction_name}"）
      - attraction_information: 提取的实用信息（可以是文本字符串或结构化对象，见下方）
      - popularity_score: 热度分数（点赞数 + 收藏数*2）

      📌 attraction_information 格式要求：

      ✅ 返回纯文本格式，清晰简洁地描述知识点

      示例：
      "门票：成人60元，学生30元，需提前3天在官网预约。开放时间：8:00-17:00。交通：地铁1号线天安门东站、公交1路。建议早上8点前到达避开人流。"

      💡 建议的信息分类（可选，根据实际情况灵活组织）：
      • 🎫 门票信息：价格、优惠政策、购票方式
      • ⏰ 时间信息：开放时间、最佳游玩时间、建议游玩时长
      • 🚗 交通攻略：如何到达、停车信息、交通方式建议
      • 📸 打卡点：最佳拍照地点、推荐机位
      • 🍜 美食推荐：景区内外特色美食、餐厅推荐
      • ⚠️  避坑指南：不建议做什么、需要注意什么
      • 💡 游玩建议：路线规划、游玩顺序、省时技巧
      • 🏨 住宿建议：附近酒店、民宿推荐

      🎯 提取示例：
      ❌ 错误："故宫太美了！强烈推荐大家来！"（无用的主观感受）
      ✅ 正确："门票成人60元，学生证半价30元，需提前3天在官网预约。建议早上8点前到达避开人流。"

      ❌ 错误："今天和闺蜜一起去故宫玩，拍了好多美照"（流水账）
      ✅ 正确："最佳打卡点在午门，建议穿红色衣服拍照。从午门进入后先走右侧路线，人相对较少。"

      ❌ 错误："交通很方便，可以坐地铁或公交"（信息不具体）
      ✅ 正确："交通：地铁1号线天安门东站B口出，步行5分钟；或乘坐公交1路、2路在天安门东站下车。停车位较少，建议公共交通出行。"

   c. 使用 Send keys: Escape 操作关闭笔记
   d. 继续处理下一篇笔记，直到收集 {max_notes} 条知识点

4. 浏览多篇笔记（建议5-8篇），提取{max_notes}条不同类型的知识点

登录/验证码处理：
- 遇到登录要求：停留在登录页面（不要尝试跳过或关闭，系统会暂停等待人工登录）
- 遇到验证码：停留在验证码页面（系统会暂停等待人工处理）
- 遇到弹窗/引导：使用 click 操作先关闭它们

输出要求：
- 使用 extract 操作输出结构化 JSON 格式数据
- 每条知识点必须包含：attraction_name, attraction_information, popularity_score
- attraction_information 必须是**纯文本字符串**，要求：
  * 信息具体、清晰、实用
  * 包含关键细节（价格、时间、地点等具体数据）
  * 避免主观感受和流水账
  * 多个信息点用句号或分号分隔
- 确保每条知识点聚焦一个主题（门票、交通、美食等）
"""


class PlannerPrompts:
    """旅行规划 Agent 提示词"""

    @staticmethod
    def generate_trip_plan(departure: str, destination: str, days: int, attractions_summary: str) -> str:
        """生成旅行规划提示词"""
        return f"""你是一位专业的旅行规划师。请根据以下收集的旅行数据,生成一份详细、实用的旅行计划。

**旅行基本信息**:
- 出发地: {departure}
- 目的地: {destination}
- 天数: {days} 天

**收集的景点数据**:
{attractions_summary}

请生成一份包含以下内容的旅行计划:

1. **每日详细行程**:
   - 每天的具体安排(上午/下午/晚上)
   - 游览时间建议
   - 交通方式
   - 用餐建议

2. **实用信息**:
   - 每个景点的门票、开放时间等关键信息
   - 交通攻略
   - 注意事项和避坑指南

3. **旅行贴士**: 实用的旅行建议

4. **预算估算**: 大致的花费预估

**输出要求**:
- 使用 Markdown 格式
- 结构清晰,便于阅读
- 信息具体实用
- 语气友好专业
"""




