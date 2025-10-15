"""Scrapers Module

爬虫模块，包含所有数据收集器和相关数据模型。
"""

# 导出爬虫类
from app.scrapers.browser_use_scraper import BrowserUseScraper
from app.scrapers.xhs_scraper import XHSScraper

# 导出爬虫数据模型
from app.scrapers.models import (
    XHSAttractionInformation,
    XHSAttractionInformationCollection,
    XHSAttractionRecommendation,
    XHSAttractionRecommendationCollection,
)

__all__ = [
    # 爬虫类
    "BrowserUseScraper",
    "XHSScraper",
    # 数据模型
    "XHSAttractionInformation",
    "XHSAttractionInformationCollection",
    "XHSAttractionRecommendation",
    "XHSAttractionRecommendationCollection",
]
