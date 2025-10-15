"""
景点数据模型 - 混合模式设计

这个模块定义了景点相关的数据模型,采用"基础字段 + AI 上下文"的混合设计模式。

设计思路:
---------
1. 保留必要的结构化字段(name, city等),方便查询和基础操作
2. 使用灵活的 context 字典存储 AI 分析结果和原始爬取数据
3. 平衡了数据库查询效率和 AI 处理的灵活性

使用示例:
---------
    # 创建景点
    attraction = Attraction(
        name="故宫",
        city="北京",
        category="历史文化",
        description="明清两代的皇家宫殿",
        address="北京市东城区景山前街4号"
    )

    # 添加原始爬取数据
    attraction.add_raw_data("xiaohongshu", {
        "notes": [...],  # 小红书笔记列表
        "total_likes": 10000
    })

    # 添加 AI 分析结果
    attraction.set_ai_analysis("summary", "适合带孩子游玩,建议预留3-4小时")
    attraction.set_ai_analysis("best_season", "春秋两季")

    # 获取数据
    summary = attraction.get_context("ai_analysis.summary")
    raw_data = attraction.get_context("raw_data.xiaohongshu")

    # 导出为字典
    data = attraction.to_dict()
"""

from typing import Any, Dict, Optional
from datetime import datetime


class Attraction:
    """
    景点数据模型

    属性说明:
    --------
    基础字段 (结构化,可直接查询):
        name: str - 景点名称
        city: str - 所属城市
        category: Optional[str] - 景点分类(历史文化/自然风光/娱乐休闲等)
        description: Optional[str] - 景点简介
        address: Optional[str] - 详细地址
        opening_hours: Optional[str] - 开放时间
        ticket_price: Optional[str] - 门票价格(支持"免费"、"50元起"等文本)
        created_at: datetime - 创建时间

    AI 上下文字段 (灵活,由 AI 动态填充):
        context: Dict[str, Any] - 包含三个主要部分:
            - raw_data: 原始爬取数据(小红书、官网等)
            - ai_analysis: AI 提取的关键信息和分析结果
            - metadata: 元数据(数据源、更新时间等)

    设计理念:
    --------
    - 基础字段用于快速查询和展示
    - context 用于存储复杂的、非结构化的数据
    - AI 可以在 context 中自由添加任何有用的信息
    """

    def __init__(
        self,
        name: str,
        city: str,
        category: Optional[str] = None,
        description: Optional[str] = None,
        address: Optional[str] = None,
        opening_hours: Optional[str] = None,
        ticket_price: Optional[str] = None
    ):
        """
        初始化景点对象

        参数:
        ----
        name: 景点名称 (必填)
        city: 所属城市 (必填)
        category: 景点分类,如 "历史文化"、"自然风光"
        description: 景点简介
        address: 详细地址
        opening_hours: 开放时间,如 "8:00-18:00"
        ticket_price: 门票价格,如 "60元"、"免费"
        """
        # 基础固定字段
        self.name = name
        self.city = city
        self.category = category

        # 常见描述性字段
        self.description = description
        self.address = address
        self.opening_hours = opening_hours
        self.ticket_price = ticket_price

        self.created_at = datetime.now()

        # AI 驱动的灵活上下文
        # 这个字典可以存储任意结构的数据
        self.context: Dict[str, Any] = {
            "raw_data": {},      # 原始爬取数据,按来源分类
            "ai_analysis": {},   # AI 提取的关键信息和分析
            "metadata": {}       # 元数据,如数据来源、更新时间等
        }

    def add_raw_data(self, source: str, data: Any):
        """
        添加原始数据源

        用于存储从各个平台爬取的原始数据,保留完整信息供 AI 分析

        参数:
        ----
        source: 数据源名称,如 "xiaohongshu", "official_website", "meituan"
        data: 任意格式的数据,可以是字典、列表等

        示例:
        ----
        attraction.add_raw_data("xiaohongshu", {
            "notes": [
                {"title": "故宫一日游攻略", "likes": 1000, ...},
                {"title": "故宫拍照指南", "likes": 800, ...}
            ],
            "avg_rating": 4.8
        })
        """
        self.context["raw_data"][source] = data

    def set_ai_analysis(self, key: str, value: Any):
        """
        设置 AI 分析结果

        AI 从原始数据中提取的关键信息,如摘要、标签、推荐理由等

        参数:
        ----
        key: 分析结果的键名
        value: 分析结果的值

        示例:
        ----
        attraction.set_ai_analysis("summary", "适合带孩子游玩,建议预留3-4小时")
        attraction.set_ai_analysis("tags", ["亲子", "历史", "拍照"])
        attraction.set_ai_analysis("crowd_level", "工作日较空,周末人多")
        """
        self.context["ai_analysis"][key] = value

    def get_context(self, key: str, default=None) -> Any:
        """
        获取上下文值,支持嵌套访问

        使用点号分隔符访问嵌套字典,类似 JavaScript 的对象访问

        参数:
        ----
        key: 键名,支持嵌套访问,如 "ai_analysis.summary"
        default: 当键不存在时返回的默认值

        返回:
        ----
        对应的值,或默认值

        示例:
        ----
        # 简单访问
        raw = attraction.get_context("raw_data")

        # 嵌套访问
        summary = attraction.get_context("ai_analysis.summary")
        notes = attraction.get_context("raw_data.xiaohongshu.notes", [])
        """
        if "." in key:
            # 处理嵌套访问,如 "ai_analysis.summary"
            keys = key.split(".")
            value = self.context
            for k in keys:
                if isinstance(value, dict):
                    value = value.get(k, {})
                else:
                    return value
            return value if value != {} else default
        return self.context.get(key, default)

    def to_dict(self) -> Dict:
        """
        导出为字典格式

        用于序列化存储(如保存到数据库、JSON文件)或 API 返回

        返回:
        ----
        包含所有字段的字典

        示例:
        ----
        data = attraction.to_dict()
        # 保存到 JSON
        import json
        with open('attraction.json', 'w') as f:
            json.dump(data, f, ensure_ascii=False)
        """
        return {
            "name": self.name,
            "city": self.city,
            "category": self.category,
            "description": self.description,
            "address": self.address,
            "opening_hours": self.opening_hours,
            "ticket_price": self.ticket_price,
            "created_at": self.created_at.isoformat(),
            "context": self.context
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "Attraction":
        """
        从字典恢复对象

        用于从数据库、JSON 文件等反序列化为对象

        参数:
        ----
        data: 字典数据,通常来自 to_dict() 的输出

        返回:
        ----
        Attraction 对象

        示例:
        ----
        # 从 JSON 加载
        import json
        with open('attraction.json') as f:
            data = json.load(f)
        attraction = Attraction.from_dict(data)
        """
        obj = cls(
            name=data["name"],
            city=data["city"],
            category=data.get("category"),
            description=data.get("description"),
            address=data.get("address"),
            opening_hours=data.get("opening_hours"),
            ticket_price=data.get("ticket_price")
        )
        obj.context = data.get("context", {"raw_data": {}, "ai_analysis": {}, "metadata": {}})
        if "created_at" in data:
            obj.created_at = datetime.fromisoformat(data["created_at"])
        return obj
