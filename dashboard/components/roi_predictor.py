# -*- coding: utf-8 -*-
"""
AI 收益预测与决策框组件

显示五维雷达图、AI 综合分数、ROI 三档预测、破发概率、
大盘调节系数及行动建议卡片。
"""

from __future__ import annotations

import streamlit as st

from config import Colors
from dashboard.components.charts import create_score_radar, create_score_breakdown_bar
from data.models import IPOStock, RecommendAction
from utils.helpers import break_prob_label, format_pct, score_color


# ============================================================
# 🔮 ROI 预测卡片
# ============================================================

def render_roi_card(stock: IPOStock) -> None:
    """
    渲染 AI 收益预测与决策框。

    包含：
    - 五维雷达图
    - AI 综合分数（大号显示）
    - ROI 预测三档
    - 破发概率
    - 大盘调节系数
    - 行动建议卡片
    - AI 分析总结

    Args:
        stock: 新股数据
    """
    ai = stock.ai

    # ---- 五维雷达图 ----
    st.markdown("<div class='detail-section-title'>🕸️ 五维评分雷达</div>", unsafe_allow_html=True)
    radar_fig = create_score_radar(ai)
    st.plotly_chart(radar_fig, use_container_width=True, config={"displayModeBar": False})

    # ---- AI 综合分数大号显示 ----
    score = ai.ai_score
    if score >= 75:
        score_class = "big-score-green"
    elif score >= 50:
        score_class = "big-score-yellow"
    else:
        score_class = "big-score-red"

    st.markdown(f"""
    <div class="glass-card" style="text-align:center; padding:1rem;">
        <div style="font-size:0.8rem; color:{Colors.TEXT_SECONDARY}; margin-bottom:0.25rem;">AI 综合推荐指数</div>
        <div class="big-score {score_class}">{score:.0f}</div>
        <div style="font-size:0.75rem; color:{Colors.TEXT_MUTED};">满分 100</div>
    </div>
    """, unsafe_allow_html=True)

    # ---- 分项得分柱状图 ----
    breakdown_fig = create_score_breakdown_bar(ai)
    st.plotly_chart(breakdown_fig, use_container_width=True, config={"displayModeBar": False})

    # ---- ROI 预测三档 ----
    st.markdown("<div class='detail-section-title'>📈 首日 ROI 预测</div>", unsafe_allow_html=True)

    roi_cols = st.columns(3)
    with roi_cols[0]:
        st.markdown(f"""
        <div class="roi-card roi-optimistic">
            <div class="roi-label">🟢 乐观</div>
            <div class="roi-value" style="color:{Colors.GREEN};">{format_pct(ai.roi_optimistic, with_sign=True)}</div>
        </div>
        """, unsafe_allow_html=True)

    with roi_cols[1]:
        neutral_color = Colors.GREEN if ai.roi_neutral > 0 else Colors.RED
        st.markdown(f"""
        <div class="roi-card roi-neutral">
            <div class="roi-label">🟡 中性</div>
            <div class="roi-value" style="color:{Colors.YELLOW};">{format_pct(ai.roi_neutral, with_sign=True)}</div>
        </div>
        """, unsafe_allow_html=True)

    with roi_cols[2]:
        st.markdown(f"""
        <div class="roi-card roi-pessimistic">
            <div class="roi-label">🔴 悲观</div>
            <div class="roi-value" style="color:{Colors.RED};">{format_pct(ai.roi_pessimistic, with_sign=True)}</div>
        </div>
        """, unsafe_allow_html=True)

    # ---- 破发概率 & 大盘 Beta ----
    st.markdown("<div style='height:0.5rem;'></div>", unsafe_allow_html=True)

    info_cols = st.columns(2)
    with info_cols[0]:
        bp_label = break_prob_label(ai.break_probability)
        bp_color = Colors.GREEN if ai.break_probability <= 0.2 else (Colors.YELLOW if ai.break_probability <= 0.4 else Colors.RED)
        st.markdown(f"""
        <div class="glass-card-sm">
            <div style="font-size:0.78rem; color:{Colors.TEXT_SECONDARY};">破发概率</div>
            <div style="font-size:1.1rem; font-weight:700; color:{bp_color}; margin-top:0.2rem;">{bp_label}</div>
        </div>
        """, unsafe_allow_html=True)

    with info_cols[1]:
        beta = ai.market_beta_applied
        beta_color = Colors.GREEN if beta >= 1.0 else (Colors.YELLOW if beta >= 0.8 else Colors.RED)
        st.markdown(f"""
        <div class="glass-card-sm">
            <div style="font-size:0.78rem; color:{Colors.TEXT_SECONDARY};">大盘调节系数 (β)</div>
            <div style="font-size:1.1rem; font-weight:700; color:{beta_color}; margin-top:0.2rem;">×{beta:.2f}</div>
            <div style="font-size:0.7rem; color:{Colors.TEXT_MUTED};">ROI 已乘以此系数</div>
        </div>
        """, unsafe_allow_html=True)

    # ---- 行动建议卡片 ----
    st.markdown("<div style='height:0.5rem;'></div>", unsafe_allow_html=True)
    _render_action_card(stock)

    # ---- AI 分析总结 ----
    if ai.analysis_summary:
        st.markdown(f"""
        <div class="glass-card-sm" style="margin-top:0.5rem;">
            <div style="font-size:0.78rem; color:{Colors.TEXT_SECONDARY}; margin-bottom:0.3rem;">🤖 AI 分析总结</div>
            <div style="font-size:0.85rem; color:{Colors.TEXT_PRIMARY}; line-height:1.6;">{ai.analysis_summary}</div>
        </div>
        """, unsafe_allow_html=True)


def _render_action_card(stock: IPOStock) -> None:
    """
    渲染行动建议卡片（大字 + 颜色背景 + 推荐理由）。

    Args:
        stock: 新股数据
    """
    ai = stock.ai
    rec = ai.recommendation

    # 根据建议等级设置样式
    if rec == RecommendAction.FULL_BUY:
        bg = f"rgba(0, 230, 118, 0.12)"
        border_color = "rgba(0, 230, 118, 0.35)"
        text_color = Colors.GREEN
        emoji = "🟢"
    elif rec == RecommendAction.ONE_LOT:
        bg = f"rgba(255, 214, 0, 0.12)"
        border_color = "rgba(255, 214, 0, 0.35)"
        text_color = Colors.YELLOW
        emoji = "🟡"
    else:
        bg = f"rgba(255, 82, 82, 0.12)"
        border_color = "rgba(255, 82, 82, 0.35)"
        text_color = Colors.RED
        emoji = "🔴"

    st.markdown(f"""
    <div style="
        background: {bg};
        border: 1px solid {border_color};
        border-radius: 14px;
        padding: 1.2rem;
        text-align: center;
    ">
        <div style="font-size:0.78rem; color:{Colors.TEXT_SECONDARY}; margin-bottom:0.5rem;">📣 行动建议</div>
        <div style="font-size:1.8rem; font-weight:800; color:{text_color};">
            {emoji} {rec.value}
        </div>
        <div style="
            font-size:0.82rem;
            color:{Colors.TEXT_PRIMARY};
            margin-top:0.75rem;
            line-height:1.65;
            text-align:left;
            padding:0 0.5rem;
        ">
            {ai.recommendation_text}
        </div>
    </div>
    """, unsafe_allow_html=True)
