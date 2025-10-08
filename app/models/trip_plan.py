"""
旅行规划模型 - 完全 AI 驱动设计

这个模块定义了旅行规划的核心数据模型,采用完全 AI 驱动的设计理念。

设计思路:
---------
1. 最小化固定字段: 只保留必要的标识信息(ID、目的地等)
2. 最大化灵活性: 所有规划决策都由 AI 在 context 中自由组织
3. 不预设结构: 不限定"几天几夜"、"几个景点"等固定格式
4. 上下文驱动: AI 基于收集的数据(景点、酒店、交通)进行综合分析和规划

为什么这样设计?
--------------
传统的旅行规划模型会预设固定字段,如:
- daily_itineraries: List[DailyItinerary]  # 预设按天组织
- estimated_budget: Dict[str, float]        # 预设预算分类
- recommended_hotel: Hotel                  # 预设推荐单个酒店

这些固定结构限制了 AI 的灵活性。实际上:
- AI 可能想推荐"松散型"行程,不按天严格划分
- 预算分析可能有多种维度,不只是"交通/住宿/门票"
- 可能推荐多个酒店组合,或根据行程分段推荐

因此,新设计让 AI 完全自由地在 context 中组织规划内容。

使用示例:
---------
    # 1. 创建规划
    plan = TripPlan(
        plan_id="trip_001",
        destination="北京",
        title="北京5日游"
    )

    # 2. 添加收集的数据
    plan.add_attraction(attraction1)
    plan.add_attraction(attraction2)
    plan.add_hotel(hotel1)
    plan.add_transport(flight_out)
    plan.add_transport(flight_return)

    # 3. 设置用户偏好
    plan.set_user_preference("budget", 5000)
    plan.set_user_preference("travel_style", "休闲")
    plan.set_user_preference("interests", ["历史", "美食"])

    # 4. AI 生成规划(由 AI Agent 调用)
    ai_planning = {
        "itinerary": {
            "day1": {"morning": "...", "afternoon": "...", "evening": "..."},
            "day2": {...}
        },
        "budget_analysis": {
            "total": 4800,
            "breakdown": {...}
        },
        "recommendations": {
            "hotels": ["推荐酒店A", "推荐酒店B"],
            "routes": "建议路线..."
        },
        "tips": ["提示1", "提示2"]
    }
    plan.set_ai_planning(ai_planning)

    # 5. 导出
    data = plan.to_dict()

核心理念:
--------
数据收集 → AI 分析 → 灵活输出
"""

from typing import Any, Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class DailyItinerary(BaseModel):
    """每日行程模型"""
    day: int = Field(description="第几天")
    date: Optional[str] = Field(default=None, description="日期")
    title: str = Field(default="", description="当天主题")
    morning: str = Field(default="", description="上午安排")
    afternoon: str = Field(default="", description="下午安排")
    evening: str = Field(default="", description="晚上安排")
    meals: List[str] = Field(default_factory=list, description="餐饮推荐")
    accommodation: str = Field(default="", description="住宿")
    notes: str = Field(default="", description="注意事项")


class TripPlan:
    """
    旅行规划数据模型 - 完全 AI 驱动

    属性说明:
    --------
    基础字段 (最小化,仅用于标识):
        plan_id: str - 规划唯一标识符
        destination: str - 目的地
        title: str - 规划标题
        created_at: datetime - 创建时间
        updated_at: datetime - 最后更新时间

    核心字段 (完全灵活):
        context: Dict[str, Any] - 包含四个主要部分:

            1. collected_data: 收集的原始数据
               - attractions: List[Attraction] - 景点列表
               - hotels: List[Hotel] - 酒店列表
               - transports: List[Transport] - 交通列表
               - other_info: Dict - 其他信息(天气、节日等)

            2. ai_planning: AI 生成的规划内容
               AI 可以自由组织任何结构,常见的包括:
               - itinerary: 行程安排(可以按天、按主题等任意组织)
               - budget: 预算分析(可以有多种分析维度)
               - recommendations: 推荐内容(酒店、路线、餐饮等)
               - analysis: 综合分析(优缺点、适合人群等)
               - tips: 旅行贴士
               - alternatives: 备选方案
               注意: 这些只是示例,AI 可以添加任何它认为有用的信息

            3. user_preferences: 用户偏好和约束
               - budget: 预算限制
               - days: 天数
               - travel_style: 旅行风格(休闲/紧凑/深度游等)
               - interests: 兴趣点
               - constraints: 约束条件(带老人/带小孩/节假日等)

            4. metadata: 元数据
               - version: 规划版本号
               - ai_model: 使用的 AI 模型
               - planning_strategy: 规划策略
               - data_sources: 数据来源

    设计理念:
    --------
    1. 数据与规划分离
       - collected_data 存储收集的原始数据
       - ai_planning 存储 AI 的规划结果
       - 清晰的职责划分

    2. AI 完全自由
       - 不限制 ai_planning 的结构
       - AI 可以根据数据和用户偏好灵活决定输出内容
       - 支持多样化的规划风格

    3. 可追溯性
       - 保留所有原始数据
       - 可以重新规划或调整
       - 便于调试和优化

    工作流程:
    --------
    1. 创建 TripPlan 对象
    2. 调用爬虫收集数据 → add_attraction/add_hotel/add_transport
    3. 设置用户偏好 → set_user_preference
    4. AI Agent 分析数据 → set_ai_planning
    5. 导出或展示规划 → to_dict
    """

    def __init__(
        self,
        plan_id: str,
        destination: str,
        title: Optional[str] = None
    ):
        """
        初始化旅行规划对象

        参数:
        ----
        plan_id: 规划唯一标识符,如 "trip_001"、"beijing_2024_spring"
        destination: 目的地,如 "北京"、"云南"
        title: 规划标题,如 "北京5日深度游",不提供则自动生成

        示例:
        ----
        plan = TripPlan(
            plan_id="trip_20240320",
            destination="成都",
            title="成都美食之旅"
        )
        """
        # 最小化基础字段
        self.plan_id = plan_id
        self.destination = destination
        self.title = title or f"{destination}旅行规划"
        self.created_at = datetime.now()
        self.updated_at = datetime.now()

        # 核心: 完全灵活的 AI 上下文
        self.context: Dict[str, Any] = {
            # 1. 收集的原始数据
            "collected_data": {
                "attractions": [],      # Attraction 对象列表
                "hotels": [],           # Hotel 对象列表
                "transports": [],       # Transport 对象列表
                "other_info": {}        # 其他信息(天气、活动等)
            },

            # 2. AI 规划和分析
            # AI 完全自由决定结构,可能包括但不限于:
            # - itinerary: 行程安排
            # - budget: 预算分析
            # - recommendations: 推荐
            # - analysis: 综合分析
            # - tips: 贴士
            # - alternatives: 备选方案
            "ai_planning": {},

            # 3. 用户偏好和约束
            "user_preferences": {},

            # 4. 元数据
            "metadata": {
                "version": 1,
                "ai_model": None,
                "planning_strategy": None,
                "data_sources": []
            }
        }

    def add_attraction(self, attraction: Any):
        """
        添加景点到收集数据

        在 AI 规划之前,先收集所有相关景点信息

        参数:
        ----
        attraction: Attraction 对象或字典

        示例:
        ----
        plan.add_attraction(attraction1)
        plan.add_attraction(attraction2)

        # 也可以直接添加字典
        plan.add_attraction({
            "name": "故宫",
            "city": "北京",
            ...
        })
        """
        self.context["collected_data"]["attractions"].append(attraction)
        self.updated_at = datetime.now()

    def add_hotel(self, hotel: Any):
        """
        添加酒店到收集数据

        参数:
        ----
        hotel: Hotel 对象或字典

        示例:
        ----
        plan.add_hotel(hotel1)
        plan.add_hotel(hotel2)
        """
        self.context["collected_data"]["hotels"].append(hotel)
        self.updated_at = datetime.now()

    def add_transport(self, transport: Any):
        """
        添加交通到收集数据

        参数:
        ----
        transport: Transport 对象或字典

        示例:
        ----
        plan.add_transport(flight_outbound)
        plan.add_transport(flight_return)
        plan.add_transport(train)
        """
        self.context["collected_data"]["transports"].append(transport)
        self.updated_at = datetime.now()

    def set_user_preference(self, key: str, value: Any):
        """
        设置用户偏好

        用于指导 AI 生成符合用户需求的规划

        参数:
        ----
        key: 偏好键名
        value: 偏好值

        常见偏好示例:
        -----------
        plan.set_user_preference("budget", 5000)  # 预算5000元
        plan.set_user_preference("days", 5)  # 5天
        plan.set_user_preference("travel_style", "休闲")  # 休闲游
        plan.set_user_preference("interests", ["历史", "美食", "拍照"])
        plan.set_user_preference("pace", "轻松")  # 节奏轻松
        plan.set_user_preference("accommodation_level", "舒适型")  # 住宿要求
        plan.set_user_preference("with_kids", True)  # 带小孩
        plan.set_user_preference("with_elderly", False)  # 不带老人
        """
        self.context["user_preferences"][key] = value
        self.updated_at = datetime.now()

    def set_ai_planning(self, planning_data: Dict[str, Any]):
        """
        设置 AI 规划结果 (完整替换)

        由 AI Agent 调用,设置整个规划内容

        参数:
        ----
        planning_data: AI 生成的规划数据,结构完全自由

        AI 规划示例:
        ----------
        planning_data = {
            # 行程安排(可以按天、按主题等任意组织)
            "itinerary": {
                "day1": {
                    "date": "2024-03-20",
                    "theme": "初识北京",
                    "morning": {
                        "activity": "故宫参观",
                        "duration": "3小时",
                        "tips": "提前预约,8点入场人少"
                    },
                    "afternoon": {...},
                    "evening": {...}
                },
                "day2": {...}
            },

            # 预算分析(可以有多种分析维度)
            "budget": {
                "total_estimated": 4800,
                "breakdown": {
                    "transportation": 1500,
                    "accommodation": 2000,
                    "food": 800,
                    "tickets": 500
                },
                "per_person": 4800,
                "savings_tips": ["提前订票", "选择地铁出行"]
            },

            # 推荐内容
            "recommendations": {
                "must_visit": ["故宫", "长城", "颐和园"],
                "hotels": ["推荐酒店A", "推荐酒店B"],
                "food": ["全聚德烤鸭", "护国寺小吃"],
                "routes": "地铁4号线沿线游玩"
            },

            # 综合分析
            "analysis": {
                "pros": ["行程松散", "价格合理", "覆盖主要景点"],
                "cons": ["景点距离较远"],
                "suitable_for": "家庭出游、首次来北京"
            },

            # 旅行贴士
            "tips": [
                "提前3天预约故宫门票",
                "长城推荐慕田峪,人少风景好",
                "地铁卡必备"
            ],

            # 备选方案
            "alternatives": {
                "budget_plan": "经济版方案...",
                "luxury_plan": "豪华版方案..."
            }
        }

        注意:
        ----
        - 上述结构只是示例,AI 可以完全自由组织
        - 可以添加任何 AI 认为有用的字段
        - 可以使用不同的组织方式(按主题、按区域等)
        """
        self.context["ai_planning"] = planning_data
        self.updated_at = datetime.now()

    def update_ai_planning(self, key: str, value: Any):
        """
        更新 AI 规划中的某个部分 (部分更新)

        用于微调或增量更新规划内容

        参数:
        ----
        key: 要更新的部分
        value: 新的值

        示例:
        ----
        # 只更新预算部分
        plan.update_ai_planning("budget", {
            "total_estimated": 5000,
            ...
        })

        # 只更新贴士
        plan.update_ai_planning("tips", [
            "新的提示1",
            "新的提示2"
        ])
        """
        self.context["ai_planning"][key] = value
        self.updated_at = datetime.now()

    def get(self, key: str, default=None) -> Any:
        """
        获取上下文值,支持嵌套访问

        使用点号分隔符访问嵌套字典

        参数:
        ----
        key: 键名,支持嵌套访问
        default: 默认值

        示例:
        ----
        # 获取收集的景点数据
        attractions = plan.get("collected_data.attractions")

        # 获取 AI 规划的行程
        itinerary = plan.get("ai_planning.itinerary")

        # 获取用户预算
        budget = plan.get("user_preferences.budget", 0)

        # 获取某天的行程
        day1 = plan.get("ai_planning.itinerary.day1")

        # 获取预算总额
        total = plan.get("ai_planning.budget.total_estimated")
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

    def set(self, key: str, value: Any):
        """
        设置上下文值,支持嵌套设置

        参数:
        ----
        key: 键名,支持嵌套设置
        value: 值

        示例:
        ----
        # 设置元数据
        plan.set("metadata.ai_model", "gpt-4")
        plan.set("metadata.planning_strategy", "balanced")

        # 设置其他信息
        plan.set("collected_data.other_info.weather", "晴天")
        plan.set("collected_data.other_info.festivals", ["春节"])

        # 微调 AI 规划
        plan.set("ai_planning.itinerary.day1.notes", "注意事项...")
        """
        if "." in key:
            keys = key.split(".")
            current = self.context
            for k in keys[:-1]:
                if k not in current:
                    current[k] = {}
                current = current[k]
            current[keys[-1]] = value
        else:
            self.context[key] = value
        self.updated_at = datetime.now()

    def to_dict(self) -> Dict:
        """
        导出完整规划为字典

        将所有数据(包括对象)转换为可序列化的字典格式

        返回:
        ----
        包含完整规划的字典

        用途:
        ----
        - 保存到数据库
        - 导出为 JSON 文件
        - API 响应
        - 前端展示

        示例:
        ----
        # 导出为 JSON
        import json
        data = plan.to_dict()
        with open('trip_plan.json', 'w') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        # 或通过 API 返回
        return jsonify(plan.to_dict())
        """
        # 转换收集的对象为字典
        collected_data = self.context["collected_data"].copy()

        # 转换景点列表
        if "attractions" in collected_data:
            collected_data["attractions"] = [
                attr.to_dict() if hasattr(attr, "to_dict") else attr
                for attr in collected_data["attractions"]
            ]

        # 转换酒店列表
        if "hotels" in collected_data:
            collected_data["hotels"] = [
                hotel.to_dict() if hasattr(hotel, "to_dict") else hotel
                for hotel in collected_data["hotels"]
            ]

        # 转换交通列表
        if "transports" in collected_data:
            collected_data["transports"] = [
                trans.to_dict() if hasattr(trans, "to_dict") else trans
                for trans in collected_data["transports"]
            ]

        return {
            "plan_id": self.plan_id,
            "destination": self.destination,
            "title": self.title,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "context": {
                "collected_data": collected_data,
                "ai_planning": self.context["ai_planning"],
                "user_preferences": self.context["user_preferences"],
                "metadata": self.context["metadata"]
            }
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "TripPlan":
        """
        从字典恢复对象

        用于从数据库、JSON 文件等加载规划

        参数:
        ----
        data: 字典数据,通常来自 to_dict() 的输出

        返回:
        ----
        TripPlan 对象

        注意:
        ----
        恢复的对象中,collected_data 里的景点、酒店、交通
        都是字典格式,不是对象。如需要对象,需要手动转换:

        plan = TripPlan.from_dict(data)
        attractions = [
            Attraction.from_dict(a)
            for a in plan.get("collected_data.attractions", [])
        ]

        示例:
        ----
        # 从 JSON 加载
        import json
        with open('trip_plan.json') as f:
            data = json.load(f)
        plan = TripPlan.from_dict(data)
        """
        obj = cls(
            plan_id=data["plan_id"],
            destination=data["destination"],
            title=data.get("title")
        )
        if "context" in data:
            obj.context = data["context"]
        if "created_at" in data:
            obj.created_at = datetime.fromisoformat(data["created_at"])
        if "updated_at" in data:
            obj.updated_at = datetime.fromisoformat(data["updated_at"])
        return obj
