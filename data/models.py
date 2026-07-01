# -*- coding: utf-8 -*-
"""
Pydantic v2 数据模型定义

定义港股 IPO 看板中所有核心数据结构，包含：
- IPOStock：单只新股的完整画像
- CornerstoneInvestor：基石投资者
- SponsorRecord：保荐人战绩
- MarketSentiment：市场情绪快照
- MarketCondition：大盘状态（用于计算 MarketBeta）
- AIAnalysis：AI 分析结果
- DashboardState：看板全局状态
"""

from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, computed_field


# ============================================================
# 🏷️ 枚举定义
# ============================================================

class HeatLevel(str, Enum):
    """散户讨论热度等级"""
    HIGH = "🔥 高"
    MEDIUM = "🟡 中"
    LOW = "🔵 低"


class RecommendAction(str, Enum):
    """AI 行动建议等级"""
    FULL_BUY = "全力申购"
    ONE_LOT = "现金一手摸"
    SKIP = "放弃"


class DataMode(str, Enum):
    """数据获取模式"""
    DEMO = "demo"
    LIVE = "live"


class MarketTrend(str, Enum):
    """大盘趋势方向"""
    BULL = "牛市"
    NEUTRAL = "震荡"
    BEAR = "熊市"


# ============================================================
# 📦 子模型
# ============================================================

class CornerstoneInvestor(BaseModel):
    """基石投资者"""
    name: str = Field(..., description="投资者名称（如：高瓴资本）")
    amount_hkd: float = Field(..., description="认购金额（港元）")
    pct: float = Field(..., ge=0, le=100, description="占发行总额的百分比")


class SponsorRecord(BaseModel):
    """保荐人历史战绩"""
    name: str = Field(..., description="保荐人名称")
    projects_2yr: int = Field(0, ge=0, description="近两年保荐项目总数")
    break_rate_2yr: float = Field(0.0, ge=0, le=1, description="近两年首日破发率（0-1）")
    avg_return_2yr: float = Field(0.0, description="近两年保荐项目首日平均涨幅（%）")


class MarketSentiment(BaseModel):
    """市场情绪快照"""
    margin_subscription_multiple: Optional[float] = Field(
        None, ge=0, description="孖展认购倍数"
    )
    retail_heat: HeatLevel = Field(
        HeatLevel.MEDIUM, description="散户讨论热度"
    )
    sentiment_summary: str = Field(
        "", description="舆情关键词摘要（如：AI概念火热、大行力推）"
    )
    data_source: str = Field(
        "", description="数据来源说明（如：综合富途/辉立数据）"
    )


class MarketCondition(BaseModel):
    """
    大盘状态 —— 用于计算 MarketBeta 调节系数。

    当恒生指数 / 恒生科技指数处于连跌趋势时，
    对整体 ROI 预测进行等比例下修，让预测更具防守性。
    """
    hsi_close: Optional[float] = Field(
        None, description="恒生指数最新收盘价"
    )
    hstech_close: Optional[float] = Field(
        None, description="恒生科技指数最新收盘价"
    )
    hsi_change_5d: Optional[float] = Field(
        None, description="恒指近5日涨跌幅（%）"
    )
    hsi_change_20d: Optional[float] = Field(
        None, description="恒指近20日涨跌幅（%）"
    )
    trend: MarketTrend = Field(
        MarketTrend.NEUTRAL, description="大盘趋势判断"
    )
    market_beta: float = Field(
        1.0, ge=0.5, le=1.2,
        description=(
            "大盘调节系数（0.5-1.2）。"
            "牛市上修至1.2，中性=1.0，极度熊市下修至0.5。"
            "直接乘以 ROI 预测值来调节最终输出。"
        )
    )
    snapshot_date: date = Field(
        default_factory=date.today, description="快照日期"
    )


class AIAnalysis(BaseModel):
    """AI 量化分析结果"""

    # ---- 各维度分项得分（0-100）----
    score_fundamental: float = Field(0, ge=0, le=100, description="基本面得分")
    score_cornerstone: float = Field(0, ge=0, le=100, description="基石投资者得分")
    score_sponsor: float = Field(0, ge=0, le=100, description="保荐人得分")
    score_sentiment: float = Field(0, ge=0, le=100, description="市场情绪得分")
    score_pricing: float = Field(0, ge=0, le=100, description="定价合理性得分")

    # ---- 综合得分 ----
    ai_score: float = Field(0, ge=0, le=100, description="AI 综合推荐指数（0-100）")

    # ---- ROI 预测（已乘以 MarketBeta）----
    roi_optimistic: float = Field(0, description="乐观 ROI（%）")
    roi_neutral: float = Field(0, description="中性 ROI（%）")
    roi_pessimistic: float = Field(0, description="悲观 ROI（%）")
    market_beta_applied: float = Field(
        1.0, description="实际应用的大盘调节系数"
    )

    # ---- 风险指标 ----
    break_probability: float = Field(
        0, ge=0, le=1, description="首日破发概率（0-1）"
    )

    # ---- 行动建议 ----
    recommendation: RecommendAction = Field(
        RecommendAction.SKIP, description="行动建议等级"
    )
    recommendation_text: str = Field(
        "", description="通俗易懂的行动建议文字说明"
    )
    analysis_summary: str = Field(
        "", description="AI 分析总结（2-3 句话）"
    )


# ============================================================
# 📊 核心主模型
# ============================================================

class IPOStock(BaseModel):
    """
    单只新股的完整画像。

    这是看板中最核心的数据模型，由 Orchestrator 汇总所有子 Agent
    的输出后构建。存入 st.session_state 后，所有前端组件均只读此模型。
    """

    # ──── 基础信息 ────
    name: str = Field(..., description="公司名称")
    code: str = Field(..., description="股票代码（如 9999.HK）")
    sector: str = Field("", description="行业赛道")
    sector_tag: str = Field("", description="赛道标签（带 emoji，如 🤖 AI）")
    subscription_start: date = Field(..., description="招股开始日")
    subscription_end: date = Field(..., description="招股截止日")
    listing_date: date = Field(..., description="上市日期")
    price_low: float = Field(..., gt=0, description="发行价下限（港元）")
    price_high: float = Field(..., gt=0, description="发行价上限（港元）")
    lot_size: int = Field(..., gt=0, description="每手股数")
    entry_fee: float = Field(..., gt=0, description="入场费 / 一手所需金额（港元）")

    # ──── 基本面 ────
    business_summary: str = Field(
        "", description="大白话主营业务描述（1-2 句话）"
    )
    revenue_ttm: Optional[float] = Field(
        None, description="近12个月收入（亿港元）"
    )
    net_profit_ttm: Optional[float] = Field(
        None, description="近12个月净利润（亿港元）"
    )
    gross_margin: Optional[float] = Field(
        None, ge=0, le=100, description="毛利率（%）"
    )

    # ──── 基石投资者 ────
    cornerstone_investors: list[CornerstoneInvestor] = Field(
        default_factory=list, description="基石投资者列表"
    )
    cornerstone_lock_up_months: int = Field(
        6, description="基石锁定期（月）"
    )

    # ──── 保荐人 ────
    sponsors: list[SponsorRecord] = Field(
        default_factory=list, description="保荐人战绩列表"
    )

    # ──── 市场情绪 ────
    sentiment: MarketSentiment = Field(
        default_factory=MarketSentiment, description="市场情绪数据"
    )

    # ──── AI 分析结果 ────
    ai: AIAnalysis = Field(
        default_factory=AIAnalysis, description="AI 量化分析结果"
    )

    # ──── 元数据 ────
    data_fetched_at: datetime = Field(
        default_factory=datetime.now, description="数据采集时间"
    )

    # ──── 计算属性 ────

    @computed_field
    @property
    def price_range_str(self) -> str:
        """发行价区间的格式化字符串"""
        return f"HK${self.price_low:.2f} - HK${self.price_high:.2f}"

    @computed_field
    @property
    def cornerstone_total_pct(self) -> float:
        """基石投资者总占比（%）"""
        return sum(inv.pct for inv in self.cornerstone_investors)

    @computed_field
    @property
    def days_until_close(self) -> int:
        """距离招股截止的天数（负数表示已截止）"""
        return (self.subscription_end - date.today()).days

    @computed_field
    @property
    def days_until_listing(self) -> int:
        """距离上市的天数（负数表示已上市）"""
        return (self.listing_date - date.today()).days

    @computed_field
    @property
    def is_subscribing(self) -> bool:
        """当前是否正在招股期内"""
        today = date.today()
        return self.subscription_start <= today <= self.subscription_end

    @computed_field
    @property
    def status_label(self) -> str:
        """当前状态标签"""
        today = date.today()
        if today < self.subscription_start:
            return "📋 即将招股"
        elif today <= self.subscription_end:
            return "🔥 正在招股"
        elif today < self.listing_date:
            return "⏳ 等待上市"
        else:
            return "✅ 已上市"

    @computed_field
    @property
    def lead_sponsor_name(self) -> str:
        """主保荐人名称（取第一个）"""
        return self.sponsors[0].name if self.sponsors else "未知"


# ============================================================
# 📋 看板全局状态
# ============================================================

class DashboardState(BaseModel):
    """
    看板全局状态，对应 st.session_state 的结构化表示。
    Orchestrator 在启动时构建此对象并一次性写入 Session。
    """
    stocks: list[IPOStock] = Field(
        default_factory=list, description="所有新股数据"
    )
    market_condition: MarketCondition = Field(
        default_factory=MarketCondition, description="大盘状态"
    )
    data_mode: DataMode = Field(
        DataMode.DEMO, description="当前数据模式"
    )
    last_refresh: datetime = Field(
        default_factory=datetime.now, description="上次刷新时间"
    )

    @computed_field
    @property
    def subscribing_count(self) -> int:
        """正在招股的新股数量"""
        return sum(1 for s in self.stocks if s.is_subscribing)

    @computed_field
    @property
    def avg_ai_score(self) -> float:
        """所有新股的平均 AI 评分"""
        if not self.stocks:
            return 0.0
        return sum(s.ai.ai_score for s in self.stocks) / len(self.stocks)
