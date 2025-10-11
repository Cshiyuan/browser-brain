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
"""


class XHSPrompts:
    """小红书爬虫提示词"""

    @staticmethod
    def search_attraction_task(attraction_name: str, max_notes: int) -> str:
        """生成搜索景点任务提示词"""
        return f"""
任务：在小红书搜索"{attraction_name}"相关的旅游笔记

具体步骤：
1. 访问小红书网站 https://www.xiaohongshu.com/search_result?keyword={attraction_name}攻略
2. 浏览搜索结果，找到前{max_notes}篇相关笔记
3. 对于每篇笔记，提取以下信息：
   - 笔记标题
   - 作者名称
   - 笔记正文内容（尽可能完整）
   - 点赞数、收藏数、评论数
   - 评论
   - 笔记中的图片URL（前3张）
   - 提取笔记中提到的URL链接（特别是官网、预订、门票相关链接）
   - 识别关键词（如：官网、官方网站、预订、门票、开放时间等）

重要提示：
- 多尝试几个帖子，单一的帖子收集不到，就换几个帖子收集
- 像真实用户一样操作，每步之间留有间隔
- 优先选择点赞数和收藏数较高的笔记
- 如果遇到登录要求，直接停留在登录页面等待（不要尝试跳过或关闭登录窗口，系统会自动检测并暂停等待人工登录）
- 遇到验证码时，停留在验证码页面（系统会自动检测并暂停等待人工处理）
- 如果遇到任何弹窗或引导，先关闭它们
- 返回结构化的JSON数据
"""

    @staticmethod
    def search_destination_guide_task(destination: str, max_attractions: int) -> str:
        """生成搜索目的地攻略任务提示词"""
        return f"""
任务：在小红书搜索"{destination}旅游攻略"或"{destination}必去景点"，提取推荐景点列表

具体步骤：
1. 访问小红书网站 https://www.xiaohongshu.com/search_result?keyword={destination}旅游攻略
2. 等待页面完全加载(3-5秒)
3. 点击浏览前5-10篇高赞攻略笔记
4. 尽量多收集景点
5. 从这些攻略笔记中提取：
   - 提到的景点名称
   - 推荐理由（为什么推荐这个景点）
   - 优先级（根据笔记中的描述判断，如"必去"=5，"推荐"=4，"可选"=3）
   - 额外信息（比如离哪些景点一起比较近）
6. 提取最多{max_attractions}个景点

重要提示：
- 多尝试几个帖子，单一的帖子收集不到，就换几个帖子收集
- 如果失败或者成功，都在msg返回，如果是失败则返回失败原因，如果是成功则简单描述。
- 优先选择点赞数和收藏数较高的攻略笔记
- 如果遇到登录要求，直接停留在登录页面等待（不要尝试跳过或关闭登录窗口，status返回login）
- 遇到验证码时，停留在验证码页面（不要尝试跳过或关闭登录窗口，status返回captcha）
- 返回结构化的JSON数据
"""


class OfficialPrompts:
    """官网爬虫提示词"""

    @staticmethod
    def get_official_info_with_links_task(attraction_name: str, collected_links: list) -> str:
        """生成带参考链接的官网信息提取任务提示词"""
        links_text = '\n'.join(['- ' + link for link in collected_links[:5]])
        return f"""
任务：查找并提取"{attraction_name}"的官方信息

已知信息：
小红书用户提供的可能的官方链接：
{links_text}

具体步骤：
1. 首先验证上述链接，找到真正的官方网站
2. 如果上述链接都不是官网，则使用百度或Google搜索"{attraction_name} 官网"
3. 访问官方网站
4. 提取以下信息：
   - 官方网站URL
   - 开放时间/营业时间
   - 门票价格（成人票、学生票、儿童票等）
   - 预订方式（网上预订、现场购票、公众号预约等）
   - 详细地址
   - 联系电话
   - 景点简介/描述

重要提示：
- 确保访问的是官方网站，而不是旅游平台
- 如果官网信息不全，可以访问景点的微信公众号或官方小程序
- 返回结构化的JSON数据
"""

    @staticmethod
    def get_official_info_without_links_task(attraction_name: str) -> str:
        """生成无参考链接的官网信息提取任务提示词"""
        return f"""
任务：查找并提取"{attraction_name}"的官方信息

具体步骤：
1. 访问百度搜索 https://www.baidu.com
2. 等待页面加载(2-3秒)
3. 在搜索框输入："{attraction_name} 官网"
4. 点击搜索或按回车
5. 等待搜索结果加载
6. 识别官方网站（优先选择.gov.cn或包含景点名称的域名）
7. 点击进入官方网站
8. 等待官网加载完成
9. 提取以下信息：
   - 官方网站URL
   - 开放时间/营业时间
   - 门票价格（成人票、学生票、儿童票等）
   - 预订方式（网上预订、现场购票、公众号预约等）
   - 详细地址
   - 联系电话
   - 景点简介/描述

重要提示：
- 像真实用户一样操作，每步之间留有间隔
- 优先选择.gov.cn或景点官方域名
- 避免打开第三方旅游平台（如携程、美团、去哪儿等）
- 如果遇到弹窗或广告，先关闭它们
- 如果百度不可用，可以尝试使用Bing搜索
- 返回结构化的JSON数据
"""
