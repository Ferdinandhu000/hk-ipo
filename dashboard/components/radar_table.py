# -*- coding: utf-8 -*-
"""
打新雷达主表组件

渲染顶部 KPI 卡片和新股列表表格。
所有状态通过 st.session_state 管理。
"""

from __future__ import annotations

import streamlit as st

from config import Colors, SessionKeys
from data.models import DashboardState, IPOStock, RecommendAction
from utils.helpers import (
    countdown_with_emoji,
    format_entry_fee,
    format_hkd,
    format_pct,
    heat_to_bar,
    score_color,
    score_emoji,
)


# ============================================================
# 📊 顶部 KPI 卡片
# ============================================================

def render_market_overview(state: DashboardState) -> None:
    """
    渲染顶部 4 个 KPI 卡片。

    显示内容：
    - 正在招股数
    - 即将上市数
    - 平均 AI 分
    - 市场热度

    Args:
        state: 看板全局状态
    """
    # 计算即将上市数（已截止但尚未上市）
    upcoming_listing = sum(
        1 for s in state.stocks
        if s.days_until_close < 0 and s.days_until_listing > 0
    )

    # 整体市场热度（取最高热度）
    heat_levels = [s.sentiment.retail_heat.value for s in state.stocks]
    if any("高" in h for h in heat_levels):
        market_heat = "🔥 高"
    elif any("中" in h for h in heat_levels):
        market_heat = "🟡 中"
    else:
        market_heat = "🔵 低"

    # 4 列布局
    cols = st.columns(4, gap="medium")

    with cols[0]:
        st.markdown(f"""
        <div class="glass-card-sm fade-in">
            <div class="kpi-label">🔥 正在招股</div>
            <div class="kpi-value">{state.subscribing_count}</div>
        </div>
        """, unsafe_allow_html=True)

    with cols[1]:
        st.markdown(f"""
        <div class="glass-card-sm fade-in">
            <div class="kpi-label">🚀 即将上市</div>
            <div class="kpi-value">{upcoming_listing}</div>
        </div>
        """, unsafe_allow_html=True)

    with cols[2]:
        avg_score = state.avg_ai_score
        color = score_color(avg_score)
        st.markdown(f"""
        <div class="glass-card-sm fade-in">
            <div class="kpi-label">🤖 平均 AI 分</div>
            <div class="kpi-value" style="-webkit-text-fill-color: {color}; background: none;">{avg_score:.0f}</div>
        </div>
        """, unsafe_allow_html=True)

    with cols[3]:
        st.markdown(f"""
        <div class="glass-card-sm fade-in">
            <div class="kpi-label">📈 市场热度</div>
            <div class="kpi-value" style="font-size:1.5rem; -webkit-text-fill-color: {Colors.TEXT_PRIMARY}; background: none;">
                {heat_to_bar(market_heat)}
            </div>
        </div>
        """, unsafe_allow_html=True)


# ============================================================
# 📋 新股列表表格
# ============================================================

def _get_action_class(recommendation: RecommendAction) -> str:
    """根据建议类型返回 CSS 类名"""
    mapping = {
        RecommendAction.FULL_BUY: "action-full-buy",
        RecommendAction.ONE_LOT: "action-one-lot",
        RecommendAction.SKIP: "action-skip",
    }
    return mapping.get(recommendation, "action-skip")


def _get_score_badge_class(score: float) -> str:
    """根据分数返回评分徽章 CSS 类名"""
    if score >= 75:
        return "score-badge score-badge-green"
    elif score >= 50:
        return "score-badge score-badge-yellow"
    else:
        return "score-badge score-badge-red"


def render_ipo_table(stocks: list[IPOStock]) -> None:
    """
    渲染新股列表表格。

    按 AI 分数降序排列，每只股票一行卡片式设计。
    点击"查看详情"按钮时，将股票代码写入 session state。

    Args:
        stocks: 新股列表
    """
    if not stocks:
        st.info("📭 暂无新股数据")
        return

    # 按 AI 分数降序排列
    sorted_stocks = sorted(stocks, key=lambda s: s.ai.ai_score, reverse=True)

    # 表头
    header_cols = st.columns([2.5, 1, 1, 1.2, 1, 1.2, 1])
    with header_cols[0]:
        st.markdown(f"<span style='color:{Colors.TEXT_SECONDARY};font-size:0.78rem;font-weight:600;'>公司</span>",
                    unsafe_allow_html=True)
    with header_cols[1]:
        st.markdown(f"<span style='color:{Colors.TEXT_SECONDARY};font-size:0.78rem;font-weight:600;'>代码</span>",
                    unsafe_allow_html=True)
    with header_cols[2]:
        st.markdown(f"<span style='color:{Colors.TEXT_SECONDARY};font-size:0.78rem;font-weight:600;'>入场费</span>",
                    unsafe_allow_html=True)
    with header_cols[3]:
        st.markdown(f"<span style='color:{Colors.TEXT_SECONDARY};font-size:0.78rem;font-weight:600;'>倒计时</span>",
                    unsafe_allow_html=True)
    with header_cols[4]:
        st.markdown(f"<span style='color:{Colors.TEXT_SECONDARY};font-size:0.78rem;font-weight:600;'>AI 分</span>",
                    unsafe_allow_html=True)
    with header_cols[5]:
        st.markdown(f"<span style='color:{Colors.TEXT_SECONDARY};font-size:0.78rem;font-weight:600;'>建议</span>",
                    unsafe_allow_html=True)
    with header_cols[6]:
        st.markdown(f"<span style='color:{Colors.TEXT_SECONDARY};font-size:0.78rem;font-weight:600;'>操作</span>",
                    unsafe_allow_html=True)

    st.markdown("<hr style='margin:0.3rem 0 0.6rem; border-color: rgba(255,255,255,0.06);'>", unsafe_allow_html=True)

    # 渲染每只股票
    for stock in sorted_stocks:
        _render_stock_row(stock)


def _render_stock_row(stock: IPOStock) -> None:
    """
    渲染单只股票的卡片行。

    Args:
        stock: 新股数据
    """
    cols = st.columns([2.5, 1, 1, 1.2, 1, 1.2, 1])

    # 公司名 + 赛道标签
    with cols[0]:
        st.markdown(f"""
        <div>
            <span class="stock-name">{stock.name}</span>
            <span class="sector-tag">{stock.sector_tag}</span>
            <br>
            <span class="stock-code">{stock.status_label}</span>
        </div>
        """, unsafe_allow_html=True)

    # 代码
    with cols[1]:
        st.markdown(f"<span style='color:{Colors.TEXT_PRIMARY};font-weight:600;font-size:0.9rem;'>{stock.code}</span>",
                    unsafe_allow_html=True)

    # 入场费
    with cols[2]:
        st.markdown(f"<span style='color:{Colors.ACCENT_CYAN};font-weight:600;font-size:0.9rem;'>{format_entry_fee(stock.entry_fee)}</span>",
                    unsafe_allow_html=True)

    # 倒计时
    with cols[3]:
        countdown_text = countdown_with_emoji(stock.subscription_end)
        st.markdown(f"<span style='font-size:0.88rem;'>{countdown_text}</span>", unsafe_allow_html=True)

    # AI 分数（带颜色徽章）
    with cols[4]:
        badge_class = _get_score_badge_class(stock.ai.ai_score)
        st.markdown(f"<span class='{badge_class}'>{stock.ai.ai_score:.0f}</span>", unsafe_allow_html=True)

    # 建议
    with cols[5]:
        action_class = _get_action_class(stock.ai.recommendation)
        emoji = score_emoji(stock.ai.ai_score)
        st.markdown(f"<span class='{action_class}'>{emoji} {stock.ai.recommendation.value}</span>",
                    unsafe_allow_html=True)

    # 详情按钮
    with cols[6]:
        if st.button("📋 详情", key=f"detail_{stock.code}", use_container_width=True):
            st.session_state[SessionKeys.SELECTED_STOCK] = stock.code

    # 行分割线
    st.markdown("<div style='height:2px;background:rgba(255,255,255,0.03);margin:0.1rem 0 0.4rem;'></div>",
                unsafe_allow_html=True)
