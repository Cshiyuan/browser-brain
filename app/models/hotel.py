"""
酒店和交通数据模型 - 混合模式设计

这个模块定义了酒店和交通相关的数据模型,同样采用"基础字段 + AI 上下文"的设计。

设计思路:
---------
1. Hotel: 保留常见的酒店属性(价格、评分等),其他信息由 AI 灵活处理
2. Transport: 统一所有交通方式(航班、火车、大巴等),不做细分
3. 使用 context 存储原始数据和 AI 分析结果

使用示例:
---------
    # 酒店示例
    hotel = Hotel(
        name="北京王府井希尔顿酒店",
        price=800.0,
        rating=4.7,
        location="王府井步行街",
        description="五星级商务酒店"
    )
    hotel.add_raw_data("ctrip", {"reviews": [...], "facilities": [...]})
    hotel.set_ai_analysis("pros", ["位置好", "早餐丰富", "服务好"])

    # 交通示例
    flight = Transport(
        transport_type="flight",
        departure="上海",
        arrival="北京",
        price=850.0,
        departure_time="2024-03-20 08:00",
        arrival_time="2024-03-20 10:30"
    )
    flight.set_ai_analysis("recommendation", "价格合理,时间段好")
"""

from typing import Any, Dict, Optional
from datetime import datetime


class Hotel:
    """
    酒店数据模型

    属性说明:
    --------
    基础字段 (结构化):
        name: str - 酒店名称
        price: Optional[float] - 每晚价格
        rating: Optional[float] - 评分(0-5分)
        location: Optional[str] - 位置描述
        description: Optional[str] - 酒店简介
        created_at: datetime - 创建时间

    AI 上下文字段 (灵活):
        context: Dict[str, Any] - 包含:
            - raw_data: 原始爬取数据(携程、美团等)
            - ai_analysis: AI 分析结果(优缺点、推荐理由等)
            - metadata: 元数据

    设计理念:
    --------
    - 保留最常用的查询字段(价格、评分)方便筛选
    - 其他详细信息(设施、评价、照片等)存在 context 中
    - AI 可以在 context 中添加任何有价值的分析
    """

    def __init__(
        self,
        name: str,
        price: Optional[float] = None,
        rating: Optional[float] = None,
        location: Optional[str] = None,
        description: Optional[str] = None
    ):
        """
        初始化酒店对象

        参数:
        ----
        name: 酒店名称 (必填)
        price: 每晚价格,单位:元
        rating: 评分,0-5分
        location: 位置描述,如 "市中心"、"靠近地铁站"
        description: 酒店简介
        """
        # 基础字段
        self.name = name
        self.price = price
        self.rating = rating
        self.location = location
        self.description = description
        self.created_at = datetime.now()

        # AI 驱动的灵活上下文
        self.context: Dict[str, Any] = {
            "raw_data": {},      # 原始爬取数据
            "ai_analysis": {},   # AI 分析结果
            "metadata": {}       # 元数据
        }

    def add_raw_data(self, source: str, data: Any):
        """
        添加原始数据

        参数:
        ----
        source: 数据源,如 "ctrip"(携程), "meituan"(美团), "booking"
        data: 原始数据

        示例:
        ----
        hotel.add_raw_data("ctrip", {
            "reviews": [{"user": "张三", "rating": 5, "comment": "很不错"}],
            "facilities": ["WiFi", "健身房", "游泳池"],
            "images": ["url1", "url2"]
        })
        """
        self.context["raw_data"][source] = data

    def set_ai_analysis(self, key: str, value: Any):
        """
        设置 AI 分析结果

        参数:
        ----
        key: 分析类型
        value: 分析内容

        示例:
        ----
        hotel.set_ai_analysis("pros", ["位置极佳", "早餐丰富", "房间宽敞"])
        hotel.set_ai_analysis("cons", ["价格稍高"])
        hotel.set_ai_analysis("best_for", "商务出行")
        hotel.set_ai_analysis("distance_to_attractions", {
            "故宫": "2公里",
            "天安门": "1.5公里"
        })
        """
        self.context["ai_analysis"][key] = value

    def get_context(self, key: str, default=None) -> Any:
        """
        获取上下文值,支持嵌套访问

        参数:
        ----
        key: 键名,支持嵌套,如 "ai_analysis.pros"
        default: 默认值

        示例:
        ----
        pros = hotel.get_context("ai_analysis.pros", [])
        reviews = hotel.get_context("raw_data.ctrip.reviews")
        """
        if "." in key:
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
        导出为字典

        返回:
        ----
        包含所有字段的字典
        """
        return {
            "name": self.name,
            "price": self.price,
            "rating": self.rating,
            "location": self.location,
            "description": self.description,
            "created_at": self.created_at.isoformat(),
            "context": self.context
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "Hotel":
        """
        从字典恢复对象

        参数:
        ----
        data: 字典数据

        返回:
        ----
        Hotel 对象
        """
        obj = cls(
            name=data["name"],
            price=data.get("price"),
            rating=data.get("rating"),
            location=data.get("location"),
            description=data.get("description")
        )
        obj.context = data.get("context", {"raw_data": {}, "ai_analysis": {}, "metadata": {}})
        if "created_at" in data:
            obj.created_at = datetime.fromisoformat(data["created_at"])
        return obj


class Transport:
    """
    交通数据模型 - 统一所有交通方式

    属性说明:
    --------
    基础字段 (结构化):
        transport_type: Optional[str] - 交通类型,如 "flight"、"train"、"bus"
                                        (仅作提示,不强制区分)
        departure: Optional[str] - 出发地
        arrival: Optional[str] - 目的地
        price: Optional[float] - 价格
        departure_time: Optional[str] - 出发时间
        arrival_time: Optional[str] - 到达时间
        created_at: datetime - 创建时间

    AI 上下文字段 (灵活):
        context: Dict[str, Any] - 包含原始数据和 AI 分析

    设计理念:
    --------
    - 不强制区分航班、火车、大巴等,统一用 Transport
    - transport_type 只是一个提示字段,AI 可以从上下文判断
    - 具体的航班号、座位等信息存在 context 中
    - 这样设计更灵活,可以支持任意交通方式(如包车、自驾等)
    """

    def __init__(
        self,
        transport_type: Optional[str] = None,
        departure: Optional[str] = None,
        arrival: Optional[str] = None,
        price: Optional[float] = None,
        departure_time: Optional[str] = None,
        arrival_time: Optional[str] = None
    ):
        """
        初始化交通对象

        参数:
        ----
        transport_type: 交通类型,如 "flight"(航班)、"train"(火车)、"bus"(大巴)
                       也可以是 "car_rental"(租车)、"charter"(包车)等
        departure: 出发地
        arrival: 目的地
        price: 价格,单位:元
        departure_time: 出发时间,建议格式 "YYYY-MM-DD HH:MM"
        arrival_time: 到达时间,建议格式 "YYYY-MM-DD HH:MM"

        示例:
        ----
        # 航班
        flight = Transport(
            transport_type="flight",
            departure="上海浦东",
            arrival="北京首都",
            price=850.0,
            departure_time="2024-03-20 08:00",
            arrival_time="2024-03-20 10:30"
        )

        # 火车
        train = Transport(
            transport_type="train",
            departure="上海虹桥",
            arrival="北京南",
            price=553.0,
            departure_time="2024-03-20 09:00",
            arrival_time="2024-03-20 14:30"
        )

        # 包车(价格可能是总价而非单人价)
        charter = Transport(
            transport_type="charter",
            departure="机场",
            arrival="酒店",
            price=200.0
        )
        """
        # 基础字段
        self.transport_type = transport_type
        self.departure = departure
        self.arrival = arrival
        self.price = price
        self.departure_time = departure_time
        self.arrival_time = arrival_time
        self.created_at = datetime.now()

        # AI 上下文
        self.context: Dict[str, Any] = {
            "raw_data": {},      # 原始数据,如航班号、车次等
            "ai_analysis": {},   # AI 分析,如推荐理由、性价比等
            "metadata": {}       # 元数据
        }

    def add_raw_data(self, source: str, data: Any):
        """
        添加原始数据

        参数:
        ----
        source: 数据源,如 "ctrip", "12306", "qunar"
        data: 原始数据

        示例:
        ----
        # 航班详情
        flight.add_raw_data("ctrip", {
            "flight_number": "CA1234",
            "airline": "中国国航",
            "aircraft": "波音737",
            "cabin_class": "经济舱",
            "baggage": "23kg",
            "meal": "有餐食"
        })

        # 火车详情
        train.add_raw_data("12306", {
            "train_number": "G123",
            "seat_type": "二等座",
            "duration": "5小时30分"
        })
        """
        self.context["raw_data"][source] = data

    def set_ai_analysis(self, key: str, value: Any):
        """
        设置 AI 分析

        参数:
        ----
        key: 分析类型
        value: 分析内容

        示例:
        ----
        transport.set_ai_analysis("recommendation", "时间段好,价格合理")
        transport.set_ai_analysis("pros", ["直飞", "准点率高", "有餐食"])
        transport.set_ai_analysis("cost_effectiveness", "高")
        transport.set_ai_analysis("suitable_for", "商务出行")
        """
        self.context["ai_analysis"][key] = value

    def get_context(self, key: str, default=None) -> Any:
        """
        获取上下文值,支持嵌套访问

        参数:
        ----
        key: 键名,支持嵌套
        default: 默认值

        示例:
        ----
        flight_no = transport.get_context("raw_data.ctrip.flight_number")
        pros = transport.get_context("ai_analysis.pros", [])
        """
        if "." in key:
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
        导出为字典

        返回:
        ----
        包含所有字段的字典
        """
        return {
            "transport_type": self.transport_type,
            "departure": self.departure,
            "arrival": self.arrival,
            "price": self.price,
            "departure_time": self.departure_time,
            "arrival_time": self.arrival_time,
            "created_at": self.created_at.isoformat(),
            "context": self.context
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "Transport":
        """
        从字典恢复对象

        参数:
        ----
        data: 字典数据

        返回:
        ----
        Transport 对象
        """
        obj = cls(
            transport_type=data.get("transport_type"),
            departure=data.get("departure"),
            arrival=data.get("arrival"),
            price=data.get("price"),
            departure_time=data.get("departure_time"),
            arrival_time=data.get("arrival_time")
        )
        obj.context = data.get("context", {"raw_data": {}, "ai_analysis": {}, "metadata": {}})
        if "created_at" in data:
            obj.created_at = datetime.fromisoformat(data["created_at"])
        return obj
