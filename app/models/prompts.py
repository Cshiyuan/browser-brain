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
    3. 使用 scroll 操作向下滚动 2 页以加载更多结果
    4. 识别相关性更高的笔记，依次选择
    5. 针对每篇笔记：
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
任务：在小红书搜索"{attraction_name}"相关的旅游笔记

具体步骤：
1. 使用 go_to_url 操作访问: https://www.xiaohongshu.com/search_result?keyword={attraction_name}攻略
2. 使用 wait 操作等待 2-3 秒确保页面加载
3. 使用 scroll 操作向下滚动 1-2 页以加载更多结果
4. 识别相关性更高的笔记，依次选择
   a. 使用 click 操作打开笔记
   b. 使用 extract 和 screenshot 操作提取以下信息：
      - 笔记标题
      - 作者名称
      - 笔记正文内容（完整）
      - 点赞数、收藏数、评论数
      - 评论内容
      - 图片URL（前3张）
      - 文中提到的URL链接（官网、预订、门票相关）
      - 关键词（官网、官方网站、预订、门票、开放时间等）
   c. 使用 Sent keys: Escape 操作关闭笔记
   d. 重复处理下一篇笔记


登录/验证码处理：
- 遇到登录要求：停留在登录页面（不要尝试跳过或关闭，系统会暂停等待人工登录）
- 遇到验证码：停留在验证码页面（系统会暂停等待人工处理）
- 遇到弹窗/引导：使用 click 操作先关闭它们

输出要求：
- 最后使用 extract 操作输出结构化 JSON 格式数据
"""




class OfficialPrompts:
    """官网爬虫提示词"""

    @staticmethod
    def get_official_info_with_links_task(attraction_name: str, collected_links: list) -> str:
        """生成带参考链接的官网信息提取任务提示词"""
        links_text = '\n'.join(['- ' + link for link in collected_links[:5]])
        return f"""
任务：查找并提取"{attraction_name}"的官方信息

已知参考链接（来自小红书用户）：
{links_text}

具体步骤：
1. 逐个验证参考链接：
   a. 使用 go_to_url 操作访问每个链接
   b. 使用 wait 操作等待 2 秒确保页面加载
   c. 使用 extract 操作检查是否为官方网站（查找 .gov.cn、官方域名或明确标识）
2. 如果没有找到有效的官方网站：
   a. 使用 go_to_url 操作访问: https://www.baidu.com
   b. 使用 input 操作搜索: "{attraction_name} 官网"
   c. 使用 click 操作点击第一个 .gov.cn 或官方域名结果
3. 进入官方网站后：
   a. 使用 extract 和 screenshot 操作提取以下信息：
      - 官方网站URL
      - 开放时间/营业时间
      - 门票价格（成人票、学生票、儿童票等）
      - 预订方式（网上预订、现场购票、公众号预约等）
      - 详细地址
      - 联系电话
      - 景点简介/描述

错误处理：
- 如果 go_to_url 操作失败：使用 refresh 操作刷新，然后重试
- 如果页面阻止访问：使用 go_back 操作返回并尝试参考列表中的下一个链接
- 如果所有尝试后仍未找到官方网站：使用 search 操作搜索 "Google {attraction_name} 官网" 作为备选

重要提示：
- 避免第三方平台（携程、美团、去哪儿）
- 优先选择 .gov.cn 或官方域名
- 如果官方网站信息不完整：在输出中注明 "部分信息不可用"

输出要求：
- 使用 extract 操作输出结构化 JSON 格式
"""

    @staticmethod
    def get_official_info_without_links_task(attraction_name: str) -> str:
        """生成无参考链接的官网信息提取任务提示词"""
        return f"""
任务：查找并提取"{attraction_name}"的官方信息

具体步骤：
1. 使用 go_to_url 操作访问: https://www.baidu.com
2. 使用 wait 操作等待 2-3 秒确保页面加载
3. 使用 input 操作输入: "{attraction_name} 官网"
4. 使用 send_keys 操作输入 "Enter" 提交搜索（或使用 click 操作点击搜索按钮）
5. 使用 wait 操作等待 2 秒加载搜索结果
6. 识别官方网站（优先选择 .gov.cn 或官方域名）
7. 使用 click 操作打开官方网站
   - 如果 click 操作失败：使用 send_keys 操作输入 "Tab Tab Enter" 进行导航
8. 使用 wait 操作等待 3 秒确保官方网站加载完成
9. 使用 extract 操作收集以下信息：
   - 官方网站URL
   - 开放时间/营业时间
   - 门票价格（成人票、学生票、儿童票等）
   - 预订方式（网上预订、现场购票、公众号预约等）
   - 详细地址
   - 联系电话
   - 景点简介/描述

错误处理：
- 如果 input 操作失败：使用 send_keys 操作直接输入搜索词
- 如果页面有弹窗/广告：使用 click 操作先关闭它们
- 如果百度不可用：使用 go_to_url 操作访问必应（Bing.com）并重试搜索
- 如果没有找到 .gov.cn 结果：使用 click 操作点击第一个看起来像官方的域名

重要提示：
- 在步骤之间使用 wait 操作（1-2 秒）模拟真实用户行为
- 避免第三方平台（携程、美团、去哪儿）- 跳过这些结果
- 优先级: .gov.cn > 官方域名 > 已验证来源

输出要求：
- 使用 extract 操作输出结构化 JSON 格式
"""
