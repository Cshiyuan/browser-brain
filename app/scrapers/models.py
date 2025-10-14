"""爬虫数据模型统一定义

所有爬虫使用的Pydantic模型都在这里定义，包括：
- 小红书相关模型（XHSNoteOutput, XHSNotesCollection, AttractionRecommendation, DestinationGuide）
- 官网相关模型（OfficialInfoOutput）
"""
from typing import List, Dict, Any
from pydantic import BaseModel, Field
class XHSAttractionInformation(BaseModel):
    """从小红书笔记中提取的景点知识点"""
    attraction_name: str = Field(default="", description="景点")
    attraction_information: str = Field(
        default="",
        description="景点有用信息（纯文本格式，清晰简洁地收集有用的旅游攻略信息）"
    )
    popularity_score: int = Field(default=0, description="热度分数（根据点赞、收藏计算）")



# ==================== 小红书相关模型 ====================


class XHSInformationCollection(BaseModel):
    """小红书笔记集合（Browser-Use AI 返回的数据结构）"""
    information: List[XHSAttractionInformation] = Field(description="信息列表")


class XHSAttractionRecommendation(BaseModel):
    """景点推荐（用于目的地攻略）"""
    name: str = Field(description="景点名称")
    reason: str = Field(default="", description="推荐理由")
    priority: int = Field(default=1, description="优先级（1-5，5最高）")
    recommended_extra_info: str = Field(default="", description="景点的额外信息")


class DestinationGuide(BaseModel):
    """目的地旅游攻略（Browser-Use AI 返回的数据结构）"""
    recommended_attractions: List[XHSAttractionRecommendation] = Field(description="推荐景点列表")
    status: str = Field(description="执行状态（success/captcha/login）")
    msg: str = Field(description="执行信息描述")

# ==================== 官网相关模型 ====================

class OfficialInfoOutput(BaseModel):
    """官网信息输出（Browser-Use AI 返回的数据结构）"""
    website: str = Field(default="", description="官方网站URL")
    opening_hours: str = Field(default="", description="开放时间")
    ticket_price: str = Field(default="", description="门票价格")
    booking_method: str = Field(default="", description="预订方式")
    address: str = Field(default="", description="地址")
    phone: str = Field(default="", description="联系电话")
    description: str = Field(default="", description="景点描述")
