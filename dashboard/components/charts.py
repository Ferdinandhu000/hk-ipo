# -*- coding: utf-8 -*-
"""
Plotly 图表工具集

所有图表统一使用暗色主题，颜色从 config.py 取值。
提供饼图、柱状图、仪表盘、雷达图、水平柱状图等图表组件。
"""

from __future__ import annotations

from typing import Optional

import plotly.graph_objects as go

from config import Colors
from data.models import AIAnalysis, CornerstoneInvestor, SponsorRecord


# ============================================================
# 🎨 统一暗色布局模板
# ============================================================

def _dark_layout(**overrides) -> dict:
    """返回统一的暗色布局配置字典"""
    base = dict(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, Noto Sans SC, sans-serif", color=Colors.TEXT_PRIMARY, size=12),
        margin=dict(l=20, r=20, t=30, b=20),
        showlegend=False,
    )
    base.update(overrides)
    return base


# ============================================================
# 🥧 基石投资者占比饼图（环形图）
# ============================================================

def create_cornerstone_pie(investors: list[CornerstoneInvestor]) -> go.Figure:
    """
    基石投资者占比饼图（环形图，中间显示总占比）。

    Args:
        investors: 基石投资者列表

    Returns:
        Plotly Figure 对象
    """
    if not investors:
        # 无数据时返回空占位图
        fig = go.Figure()
        fig.update_layout(
            **_dark_layout(),
            annotations=[dict(text="暂无基石投资者", x=0.5, y=0.5, showarrow=False,
                              font=dict(size=14, color=Colors.TEXT_SECONDARY))]
        )
        return fig

    names = [inv.name for inv in investors]
    pcts = [inv.pct for inv in investors]
    total_pct = sum(pcts)

    # 添加"其他"部分
    other_pct = max(0, 100 - total_pct)
    labels = names + ["其他（公开发售）"]
    values = pcts + [other_pct]

    # 颜色：基石用渐变紫 → 蓝系，其他用灰色
    base_colors = [
        Colors.ACCENT_PURPLE,
        Colors.ACCENT_BLUE,
        Colors.ACCENT_CYAN,
        Colors.ACCENT_PINK,
        "#A29BFE",
        "#74B9FF",
    ]
    colors = [base_colors[i % len(base_colors)] for i in range(len(names))]
    colors.append("rgba(74, 85, 104, 0.4)")  # "其他"用暗灰

    fig = go.Figure(data=[
        go.Pie(
            labels=labels,
            values=values,
            hole=0.65,
            marker=dict(colors=colors, line=dict(color=Colors.BG_PRIMARY, width=2)),
            textinfo="label+percent",
            textfont=dict(size=10, color=Colors.TEXT_PRIMARY),
            hovertemplate="<b>%{label}</b><br>占比: %{percent}<extra></extra>",
            direction="clockwise",
            sort=False,
        )
    ])

    fig.update_layout(
        **_dark_layout(
            height=280,
            annotations=[
                dict(
                    text=f"<b>{total_pct:.0f}%</b><br><span style='font-size:10px;color:{Colors.TEXT_SECONDARY}'>基石占比</span>",
                    x=0.5, y=0.5, showarrow=False,
                    font=dict(size=22, color=Colors.ACCENT_PURPLE),
                )
            ],
        )
    )
    return fig


# ============================================================
# 📊 保荐人胜率柱状图（双轴：破发率 + 平均涨幅）
# ============================================================

def create_sponsor_bar(sponsors: list[SponsorRecord]) -> go.Figure:
    """
    保荐人胜率柱状图。

    左轴（柱状图）：破发率
    右轴（折线图/标记）：平均涨幅

    Args:
        sponsors: 保荐人列表

    Returns:
        Plotly Figure 对象
    """
    if not sponsors:
        fig = go.Figure()
        fig.update_layout(
            **_dark_layout(),
            annotations=[dict(text="暂无保荐人数据", x=0.5, y=0.5, showarrow=False,
                              font=dict(size=14, color=Colors.TEXT_SECONDARY))]
        )
        return fig

    names = [s.name for s in sponsors]
    break_rates = [s.break_rate_2yr * 100 for s in sponsors]
    avg_returns = [s.avg_return_2yr for s in sponsors]

    fig = go.Figure()

    # 破发率柱状图
    fig.add_trace(go.Bar(
        x=names, y=break_rates,
        name="破发率",
        marker=dict(
            color=[Colors.RED if br > 30 else Colors.YELLOW if br > 20 else Colors.GREEN for br in break_rates],
            opacity=0.8,
            line=dict(width=0),
        ),
        text=[f"{br:.0f}%" for br in break_rates],
        textposition="outside",
        textfont=dict(color=Colors.TEXT_PRIMARY, size=11),
        yaxis="y",
        hovertemplate="<b>%{x}</b><br>破发率: %{y:.1f}%<extra></extra>",
    ))

    # 平均涨幅散点（右轴）
    fig.add_trace(go.Scatter(
        x=names, y=avg_returns,
        name="平均涨幅",
        mode="markers+text",
        marker=dict(
            size=14,
            color=[Colors.GREEN if r > 0 else Colors.RED for r in avg_returns],
            symbol="diamond",
            line=dict(width=1, color=Colors.TEXT_PRIMARY),
        ),
        text=[f"{r:+.1f}%" for r in avg_returns],
        textposition="top center",
        textfont=dict(color=Colors.TEXT_PRIMARY, size=10),
        yaxis="y2",
        hovertemplate="<b>%{x}</b><br>平均涨幅: %{y:+.1f}%<extra></extra>",
    ))

    fig.update_layout(
        **_dark_layout(
            height=280,
            showlegend=True,
            legend=dict(
                orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5,
                font=dict(size=10, color=Colors.TEXT_SECONDARY),
            ),
            yaxis=dict(
                title=dict(text="破发率 (%)", font=dict(size=10, color=Colors.TEXT_SECONDARY)),
                gridcolor="rgba(255,255,255,0.05)", zeroline=False,
                tickfont=dict(color=Colors.TEXT_SECONDARY, size=9),
            ),
            yaxis2=dict(
                title=dict(text="平均涨幅 (%)", font=dict(size=10, color=Colors.TEXT_SECONDARY)),
                overlaying="y", side="right", zeroline=False,
                tickfont=dict(color=Colors.TEXT_SECONDARY, size=9),
            ),
            xaxis=dict(tickfont=dict(color=Colors.TEXT_PRIMARY, size=10)),
            bargap=0.35,
        )
    )
    return fig


# ============================================================
# 🎛️ ROI 预测仪表盘
# ============================================================

def create_roi_gauge(
    roi_opt: float,
    roi_neutral: float,
    roi_pess: float,
    break_prob: float,
) -> go.Figure:
    """
    ROI 预测仪表盘（以中性 ROI 为主指针）。

    Args:
        roi_opt: 乐观 ROI (%)
        roi_neutral: 中性 ROI (%)
        roi_pess: 悲观 ROI (%)
        break_prob: 破发概率 (0-1)

    Returns:
        Plotly Figure 对象
    """
    # 仪表盘范围
    gauge_min = min(roi_pess, -30)
    gauge_max = max(roi_opt, 50)

    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=roi_neutral,
        number=dict(suffix="%", font=dict(size=28, color=Colors.TEXT_PRIMARY)),
        delta=dict(reference=0, suffix="%", increasing_color=Colors.GREEN, decreasing_color=Colors.RED),
        gauge=dict(
            axis=dict(range=[gauge_min, gauge_max], ticksuffix="%",
                      tickfont=dict(size=9, color=Colors.TEXT_SECONDARY)),
            bar=dict(color=Colors.ACCENT_PURPLE, thickness=0.3),
            bgcolor="rgba(30,34,50,0.3)",
            borderwidth=0,
            steps=[
                dict(range=[gauge_min, 0], color="rgba(255,82,82,0.15)"),
                dict(range=[0, gauge_max], color="rgba(0,230,118,0.1)"),
            ],
            threshold=dict(
                line=dict(color=Colors.ACCENT_CYAN, width=3),
                thickness=0.8,
                value=roi_neutral,
            ),
        ),
        title=dict(text="中性 ROI 预测", font=dict(size=13, color=Colors.TEXT_SECONDARY)),
    ))

    fig.update_layout(**_dark_layout(height=220, margin=dict(l=30, r=30, t=50, b=10)))
    return fig


# ============================================================
# 🕸️ 五维雷达图
# ============================================================

def create_score_radar(ai: AIAnalysis) -> go.Figure:
    """
    五维雷达图（基本面 / 基石 / 保荐人 / 情绪 / 定价）。

    Args:
        ai: AIAnalysis 分析结果

    Returns:
        Plotly Figure 对象
    """
    categories = ["基本面", "基石投资者", "保荐人", "市场情绪", "定价合理性"]
    values = [
        ai.score_fundamental,
        ai.score_cornerstone,
        ai.score_sponsor,
        ai.score_sentiment,
        ai.score_pricing,
    ]
    # 闭合雷达图
    categories_closed = categories + [categories[0]]
    values_closed = values + [values[0]]

    fig = go.Figure()

    # 填充区域
    fig.add_trace(go.Scatterpolar(
        r=values_closed,
        theta=categories_closed,
        fill="toself",
        fillcolor="rgba(108, 92, 231, 0.15)",
        line=dict(color=Colors.ACCENT_PURPLE, width=2),
        marker=dict(size=6, color=Colors.ACCENT_CYAN),
        hovertemplate="<b>%{theta}</b>: %{r:.0f} 分<extra></extra>",
    ))

    fig.update_layout(
        **_dark_layout(height=300),
        polar=dict(
            bgcolor="rgba(0,0,0,0)",
            radialaxis=dict(
                range=[0, 100], tickvals=[20, 40, 60, 80, 100],
                gridcolor="rgba(255,255,255,0.08)",
                linecolor="rgba(255,255,255,0.05)",
                tickfont=dict(size=8, color=Colors.TEXT_MUTED),
            ),
            angularaxis=dict(
                gridcolor="rgba(255,255,255,0.08)",
                linecolor="rgba(255,255,255,0.05)",
                tickfont=dict(size=11, color=Colors.TEXT_PRIMARY),
            ),
        ),
    )
    return fig


# ============================================================
# 📊 分项得分水平柱状图
# ============================================================

def create_score_breakdown_bar(ai: AIAnalysis) -> go.Figure:
    """
    分项得分水平柱状图（从高到低排列）。

    Args:
        ai: AIAnalysis 分析结果

    Returns:
        Plotly Figure 对象
    """
    dims = {
        "基本面": ai.score_fundamental,
        "基石投资者": ai.score_cornerstone,
        "保荐人": ai.score_sponsor,
        "市场情绪": ai.score_sentiment,
        "定价合理性": ai.score_pricing,
    }
    # 按分数排序
    sorted_dims = sorted(dims.items(), key=lambda x: x[1])
    names = [d[0] for d in sorted_dims]
    scores = [d[1] for d in sorted_dims]

    # 根据分数着色
    colors = []
    for s in scores:
        if s >= 75:
            colors.append(Colors.GREEN)
        elif s >= 50:
            colors.append(Colors.YELLOW)
        else:
            colors.append(Colors.RED)

    fig = go.Figure(go.Bar(
        x=scores,
        y=names,
        orientation="h",
        marker=dict(color=colors, opacity=0.85, line=dict(width=0)),
        text=[f"{s:.0f}" for s in scores],
        textposition="outside",
        textfont=dict(color=Colors.TEXT_PRIMARY, size=11, family="Inter"),
        hovertemplate="<b>%{y}</b>: %{x:.0f} 分<extra></extra>",
    ))

    fig.update_layout(
        **_dark_layout(height=220, margin=dict(l=80, r=40, t=10, b=10)),
        xaxis=dict(
            range=[0, 105], showgrid=True,
            gridcolor="rgba(255,255,255,0.05)",
            tickfont=dict(size=9, color=Colors.TEXT_MUTED),
        ),
        yaxis=dict(tickfont=dict(size=11, color=Colors.TEXT_PRIMARY)),
    )
    return fig
