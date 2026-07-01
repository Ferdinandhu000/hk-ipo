# -*- coding: utf-8 -*-
"""
通用工具函数模块

提供日期计算、金额格式化、倒计时渲染等看板通用工具。
"""

from datetime import date, datetime
from typing import Optional


# ============================================================
# ⏱️ 日期与倒计时
# ============================================================

def days_countdown(target_date: date) -> str:
    """
    计算距离目标日期的倒计时文字。

    Args:
        target_date: 目标日期

    Returns:
        格式化的倒计时字符串，例如：
        - "2 天后"
        - "今天"
        - "已过 3 天"
    """
    delta = (target_date - date.today()).days
    if delta > 0:
        return f"{delta} 天后"
    elif delta == 0:
        return "今天"
    else:
        return f"已过 {abs(delta)} 天"


def countdown_with_emoji(target_date: date) -> str:
    """
    带 emoji 的倒计时标签（用于看板表格）。

    Args:
        target_date: 目标日期

    Returns:
        带 emoji 的倒计时文字
    """
    delta = (target_date - date.today()).days
    if delta > 3:
        return f"📅 {delta}天"
    elif delta > 0:
        return f"⏰ {delta}天"
    elif delta == 0:
        return "🔔 今天"
    else:
        return f"✅ 已截止"


# ============================================================
# 💰 金额格式化
# ============================================================

def format_hkd(amount: float, compact: bool = False) -> str:
    """
    格式化港元金额。

    Args:
        amount: 金额（港元）
        compact: 是否使用紧凑格式（亿/万）

    Returns:
        格式化字符串，例如：
        - "HK$4,040.40"
        - "HK$3.0 亿"（紧凑模式）
    """
    if compact:
        if abs(amount) >= 1e8:
            return f"HK${amount / 1e8:.1f} 亿"
        elif abs(amount) >= 1e4:
            return f"HK${amount / 1e4:.1f} 万"
    return f"HK${amount:,.2f}"


def format_entry_fee(amount: float) -> str:
    """
    格式化入场费（一手金额），突出显示。

    Args:
        amount: 入场费（港元）

    Returns:
        格式化字符串，例如 "¥4,040"
    """
    return f"¥{amount:,.0f}"


def format_pct(value: float, decimals: int = 1, with_sign: bool = False) -> str:
    """
    格式化百分比。

    Args:
        value: 百分比数值（如 18.5 表示 18.5%）
        decimals: 小数位数
        with_sign: 是否显示正号

    Returns:
        格式化百分比字符串
    """
    sign = "+" if with_sign and value > 0 else ""
    return f"{sign}{value:.{decimals}f}%"


def format_multiple(value: Optional[float]) -> str:
    """
    格式化孖展认购倍数。

    Args:
        value: 认购倍数（None 表示暂无数据）

    Returns:
        格式化字符串，例如 "220x" 或 "暂无数据"
    """
    if value is None:
        return "暂无数据"
    if value >= 100:
        return f"🔥 {value:.0f}x"
    elif value >= 30:
        return f"📈 {value:.0f}x"
    elif value >= 10:
        return f"📊 {value:.0f}x"
    else:
        return f"📉 {value:.1f}x"


# ============================================================
# 🏷️ 标签与徽章
# ============================================================

def score_color(score: float) -> str:
    """
    根据 AI 评分返回对应颜色（十六进制）。

    Args:
        score: AI 综合评分（0-100）

    Returns:
        十六进制颜色字符串
    """
    if score >= 75:
        return "#00E676"  # 绿色
    elif score >= 50:
        return "#FFD600"  # 黄色
    else:
        return "#FF5252"  # 红色


def score_emoji(score: float) -> str:
    """
    根据 AI 评分返回对应 emoji。

    Args:
        score: AI 综合评分（0-100）

    Returns:
        emoji 字符串
    """
    if score >= 75:
        return "🟢"
    elif score >= 50:
        return "🟡"
    else:
        return "🔴"


def break_prob_label(prob: float) -> str:
    """
    破发概率的可读标签。

    Args:
        prob: 破发概率（0-1）

    Returns:
        可读标签，例如 "低风险 (12%)"
    """
    pct = prob * 100
    if pct <= 20:
        return f"🛡️ 低风险 ({pct:.0f}%)"
    elif pct <= 40:
        return f"⚠️ 中等风险 ({pct:.0f}%)"
    elif pct <= 60:
        return f"🔶 较高风险 ({pct:.0f}%)"
    else:
        return f"🚨 高风险 ({pct:.0f}%)"


def heat_to_bar(heat_level: str) -> str:
    """
    将热度等级转换为可视化条。

    Args:
        heat_level: 热度等级字符串（含 emoji）

    Returns:
        可视化热度条
    """
    if "高" in heat_level:
        return "🔥🔥🔥🔥🔥"
    elif "中" in heat_level:
        return "🟡🟡🟡⬜⬜"
    else:
        return "🔵⬜⬜⬜⬜"


# ============================================================
# 📅 时间戳
# ============================================================

def format_datetime(dt: datetime) -> str:
    """
    格式化时间戳为可读字符串。

    Args:
        dt: datetime 对象

    Returns:
        格式化字符串，例如 "2026-07-01 21:30"
    """
    return dt.strftime("%Y-%m-%d %H:%M")


def format_refresh_ago(dt: datetime) -> str:
    """
    计算距离上次刷新过了多久。

    Args:
        dt: 上次刷新时间

    Returns:
        可读的时间差，例如 "5 分钟前"、"刚刚"
    """
    delta = datetime.now() - dt
    seconds = delta.total_seconds()

    if seconds < 60:
        return "刚刚"
    elif seconds < 3600:
        return f"{int(seconds // 60)} 分钟前"
    elif seconds < 86400:
        return f"{int(seconds // 3600)} 小时前"
    else:
        return f"{int(seconds // 86400)} 天前"
