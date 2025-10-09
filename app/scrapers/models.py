"""爬虫数据模型统一定义

所有爬虫使用的Pydantic模型都在这里定义，包括：
- 小红书相关模型（XHSNoteOutput, XHSNotesCollection, AttractionRecommendation, DestinationGuide）
- 官网相关模型（OfficialInfoOutput）
"""
from typing import List
from pydantic import BaseModel, Field


# ==================== 小红书相关模型 ====================

class XHSNoteOutput(BaseModel):
    """单条小红书笔记输出（Browser-Use AI 返回的数据结构）"""
    title: str = Field(description="笔记标题")
    author: str = Field(description="作者名称")
    content: str = Field(description="笔记正文内容")
    likes: int = Field(default=0, description="点赞数")
    collects: int = Field(default=0, description="收藏数")
    comments: int = Field(default=0, description="评论数")
    extracted_links: List[str] = Field(default_factory=list, description="提取的URL链接（官网、预订链接等）")
    keywords: List[str] = Field(default_factory=list, description="关键词（官网、预订、门票等）")
    images: List[str] = Field(default_factory=list, description="图片URL列表")


class XHSNotesCollection(BaseModel):
    """小红书笔记集合（Browser-Use AI 返回的数据结构）"""
    notes: List[XHSNoteOutput] = Field(description="笔记列表")


class AttractionRecommendation(BaseModel):
    """景点推荐（用于目的地攻略）"""
    name: str = Field(description="景点名称")
    reason: str = Field(default="", description="推荐理由")
    priority: int = Field(default=1, description="优先级（1-5，5最高）")
    recommended_extra_info: str = Field(description="景点的额外信息")


class DestinationGuide(BaseModel):
    """目的地旅游攻略（Browser-Use AI 返回的数据结构）"""
    recommended_attractions: List[AttractionRecommendation] = Field(description="推荐景点列表")
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
