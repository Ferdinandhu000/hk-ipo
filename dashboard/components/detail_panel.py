# -*- coding: utf-8 -*-
"""
详情透视面板

选中某只股票后展示完整详情视图，包括：
- 左栏：公司基本面 + 财务指标
- 中栏：基石投资者饼图 + 保荐人柱状图
- 右栏：AI 收益预测与决策
- 底部：市场情绪区域
"""

from __future__ import annotations

import streamlit as st

from config import Colors, SessionKeys
from dashboard.components.charts import create_cornerstone_pie, create_sponsor_bar
from dashboard.components.roi_predictor import render_roi_card
from data.models import IPOStock
from utils.helpers import (
    countdown_with_emoji,
    format_entry_fee,
    format_hkd,
    format_multiple,
    format_pct,
    heat_to_bar,
    score_color,
)


# ============================================================
# 📋 详情面板主入口
# ============================================================

def render_detail_panel(stock: IPOStock) -> None:
    """
    渲染完整的股票详情面板。

    布局分三栏 + 底部市场情绪区域。

    Args:
        stock: 选中的新股数据
    """
    # ---- 顶部：返回按钮 + 标题 ----
    top_cols = st.columns([1, 8])
    with top_cols[0]:
        if st.button("← 返回", key="back_to_radar", use_container_width=True):
            st.session_state[SessionKeys.SELECTED_STOCK] = None
            st.rerun()

    with top_cols[1]:
        st.markdown(f"""
        <div style="display:flex; align-items:center; gap:0.8rem;">
            <span class="detail-header">{stock.name}</span>
            <span class="sector-tag" style="font-size:0.8rem;">{stock.sector_tag}</span>
            <span style="color:{Colors.TEXT_SECONDARY}; font-size:0.9rem;">{stock.code}</span>
            <span style="font-size:0.85rem;">{stock.status_label}</span>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height:0.8rem;'></div>", unsafe_allow_html=True)

    # ---- 三栏布局 ----
    left_col, mid_col, right_col = st.columns([1, 1, 1], gap="large")

    # ========================
    # 左栏：公司基本面
    # ========================
    with left_col:
        _render_fundamentals(stock)

    # ========================
    # 中栏：基石 + 保荐人
    # ========================
    with mid_col:
        _render_investors_sponsors(stock)

    # ========================
    # 右栏：AI 预测
    # ========================
    with right_col:
        render_roi_card(stock)

    # ---- 底部：市场情绪 ----
    st.markdown("<div style='height:1rem;'></div>", unsafe_allow_html=True)
    _render_sentiment(stock)


# ============================================================
# 💼 左栏：公司基本面
# ============================================================

def _render_fundamentals(stock: IPOStock) -> None:
    """渲染公司基本面卡片"""

    # ---- 基本信息 ----
    st.markdown("<div class='detail-section-title'>💼 公司概况</div>", unsafe_allow_html=True)

    st.markdown(f"""
    <div class="glass-card">
        <div style="font-size:0.85rem; color:{Colors.TEXT_PRIMARY}; line-height:1.7; margin-bottom:0.8rem;">
            {stock.business_summary}
        </div>
        <div class="finance-row">
            <span class="finance-label">发行价区间</span>
            <span class="finance-value">{stock.price_range_str}</span>
        </div>
        <div class="finance-row">
            <span class="finance-label">每手股数</span>
            <span class="finance-value">{stock.lot_size:,} 股</span>
        </div>
        <div class="finance-row">
            <span class="finance-label">入场费</span>
            <span class="finance-value" style="color:{Colors.ACCENT_CYAN};">{format_entry_fee(stock.entry_fee)}</span>
        </div>
        <div class="finance-row">
            <span class="finance-label">招股截止</span>
            <span class="finance-value">{countdown_with_emoji(stock.subscription_end)}</span>
        </div>
        <div class="finance-row">
            <span class="finance-label">上市日期</span>
            <span class="finance-value">{stock.listing_date.strftime('%Y-%m-%d')} ({countdown_with_emoji(stock.listing_date)})</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ---- 财务指标 ----
    st.markdown("<div class='detail-section-title'>📊 财务指标</div>", unsafe_allow_html=True)

    revenue_text = f"{stock.revenue_ttm:.1f} 亿" if stock.revenue_ttm is not None else "N/A"
    profit_text = f"{stock.net_profit_ttm:.1f} 亿" if stock.net_profit_ttm is not None else "N/A"
    profit_color = Colors.GREEN if (stock.net_profit_ttm or 0) > 0 else Colors.RED
    margin_text = f"{stock.gross_margin:.1f}%" if stock.gross_margin is not None else "N/A"

    st.markdown(f"""
    <div class="glass-card">
        <div class="finance-row">
            <span class="finance-label">近12月收入</span>
            <span class="finance-value">HK${revenue_text}</span>
        </div>
        <div class="finance-row">
            <span class="finance-label">近12月净利润</span>
            <span class="finance-value" style="color:{profit_color};">HK${profit_text}</span>
        </div>
        <div class="finance-row">
            <span class="finance-label">毛利率</span>
            <span class="finance-value">{margin_text}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ---- 保荐人信息摘要 ----
    st.markdown("<div class='detail-section-title'>🏦 保荐人</div>", unsafe_allow_html=True)
    for sp in stock.sponsors:
        break_color = Colors.GREEN if sp.break_rate_2yr <= 0.2 else (Colors.YELLOW if sp.break_rate_2yr <= 0.35 else Colors.RED)
        st.markdown(f"""
        <div class="glass-card-sm" style="margin-bottom:0.5rem;">
            <div style="font-weight:700; color:{Colors.TEXT_PRIMARY}; font-size:0.9rem;">{sp.name}</div>
            <div style="font-size:0.78rem; color:{Colors.TEXT_SECONDARY}; margin-top:0.2rem;">
                近2年项目: {sp.projects_2yr} 个 &nbsp;|&nbsp;
                <span style="color:{break_color};">破发率: {format_pct(sp.break_rate_2yr * 100)}</span> &nbsp;|&nbsp;
                平均涨幅: {format_pct(sp.avg_return_2yr, with_sign=True)}
            </div>
        </div>
        """, unsafe_allow_html=True)


# ============================================================
# 🥧 中栏：基石投资者 + 保荐人图表
# ============================================================

def _render_investors_sponsors(stock: IPOStock) -> None:
    """渲染基石投资者饼图和保荐人柱状图"""

    # ---- 基石投资者饼图 ----
    st.markdown("<div class='detail-section-title'>🏛️ 基石投资者</div>", unsafe_allow_html=True)

    if stock.cornerstone_investors:
        st.markdown(f"""
        <div style="font-size:0.78rem; color:{Colors.TEXT_SECONDARY}; margin-bottom:0.3rem;">
            合计占比 <b style="color:{Colors.ACCENT_PURPLE};">{stock.cornerstone_total_pct:.0f}%</b>
            &nbsp;|&nbsp; 锁定期 {stock.cornerstone_lock_up_months} 个月
        </div>
        """, unsafe_allow_html=True)

    pie_fig = create_cornerstone_pie(stock.cornerstone_investors)
    st.plotly_chart(pie_fig, use_container_width=True, config={"displayModeBar": False})

    # 基石投资者明细列表
    if stock.cornerstone_investors:
        for inv in stock.cornerstone_investors:
            st.markdown(f"""
            <div style="
                display:flex; justify-content:space-between; align-items:center;
                padding:0.3rem 0.5rem;
                border-bottom:1px solid rgba(255,255,255,0.04);
                font-size:0.8rem;
            ">
                <span style="color:{Colors.TEXT_PRIMARY}; font-weight:500;">{inv.name}</span>
                <span>
                    <span style="color:{Colors.ACCENT_CYAN};">{format_hkd(inv.amount_hkd, compact=True)}</span>
                    <span style="color:{Colors.TEXT_MUTED}; margin-left:0.4rem;">({inv.pct:.0f}%)</span>
                </span>
            </div>
            """, unsafe_allow_html=True)

    # ---- 保荐人胜率柱状图 ----
    st.markdown("<div style='height:1rem;'></div>", unsafe_allow_html=True)
    st.markdown("<div class='detail-section-title'>📊 保荐人战绩</div>", unsafe_allow_html=True)

    bar_fig = create_sponsor_bar(stock.sponsors)
    st.plotly_chart(bar_fig, use_container_width=True, config={"displayModeBar": False})


# ============================================================
# 📡 底部：市场情绪
# ============================================================

def _render_sentiment(stock: IPOStock) -> None:
    """渲染底部市场情绪区域"""
    sentiment = stock.sentiment

    st.markdown("<div class='detail-section-title'>📡 市场情绪</div>", unsafe_allow_html=True)

    cols = st.columns(3, gap="medium")

    with cols[0]:
        margin_text = format_multiple(sentiment.margin_subscription_multiple)
        st.markdown(f"""
        <div class="glass-card-sm">
            <div style="font-size:0.78rem; color:{Colors.TEXT_SECONDARY};">孖展认购倍数</div>
            <div style="font-size:1.3rem; font-weight:800; color:{Colors.ACCENT_CYAN}; margin-top:0.2rem;">
                {margin_text}
            </div>
        </div>
        """, unsafe_allow_html=True)

    with cols[1]:
        heat_bar = heat_to_bar(sentiment.retail_heat.value)
        st.markdown(f"""
        <div class="glass-card-sm">
            <div style="font-size:0.78rem; color:{Colors.TEXT_SECONDARY};">散户讨论热度</div>
            <div style="font-size:1.2rem; margin-top:0.2rem;">
                {sentiment.retail_heat.value} &nbsp; {heat_bar}
            </div>
        </div>
        """, unsafe_allow_html=True)

    with cols[2]:
        st.markdown(f"""
        <div class="glass-card-sm">
            <div style="font-size:0.78rem; color:{Colors.TEXT_SECONDARY};">舆情摘要</div>
            <div style="font-size:0.85rem; color:{Colors.TEXT_PRIMARY}; margin-top:0.25rem; line-height:1.55;">
                {sentiment.sentiment_summary}
            </div>
            <div style="font-size:0.68rem; color:{Colors.TEXT_MUTED}; margin-top:0.3rem;">
                数据来源: {sentiment.data_source}
            </div>
        </div>
        """, unsafe_allow_html=True)
