"""Scrapers Module

爬虫模块，包含所有数据收集器和相关数据模型。
"""

# 导出爬虫类
from app.scrapers.browser_use_scraper import BrowserUseScraper
from app.scrapers.xhs_scraper import XHSScraper
from app.scrapers.official_scraper import OfficialScraper

# 导出爬虫数据模型
from app.scrapers.models import (
    XHSNoteOutput,
    XHSNotesCollection,
    AttractionRecommendation,
    DestinationGuide,
    OfficialInfoOutput,
)

__all__ = [
    # 爬虫类
    "BrowserUseScraper",
    "XHSScraper",
    "OfficialScraper",
    # 数据模型
    "XHSNoteOutput",
    "XHSNotesCollection",
    "AttractionRecommendation",
    "DestinationGuide",
    "OfficialInfoOutput",
]
