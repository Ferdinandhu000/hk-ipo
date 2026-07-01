# -*- coding: utf-8 -*-
"""
港股打新雷达 · AI 智能推荐看板 —— Streamlit 主入口

功能：
- 加载暗色 Glassmorphism 主题 CSS
- Session State 初始化（一次性加载 Demo 数据）
- 侧边栏（数据模式选择、刷新、大盘状态）
- 主区域路由（雷达主表 / 详情面板）
- 底部 Footer
"""

from __future__ import annotations

import sys
from pathlib import Path

# ---- Windows GBK 编码问题修复 (处理 emoji 打印) ----
if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

# ---- 将项目根目录加入 sys.path，确保导入路径正确 ----
_project_root = Path(__file__).resolve().parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

import streamlit as st

from config import Colors, Layout, SessionKeys
from dashboard.components.detail_panel import render_detail_panel
from dashboard.components.radar_table import render_ipo_table, render_market_overview
from data.models import DashboardState, DataMode
from data.sample_data import generate_sample_dashboard_state
from agents.orchestrator import OrchestratorAgent
from utils.helpers import format_pct, format_refresh_ago

# ============================================================
# 🔧 页面配置（必须放在最前面）
# ============================================================

st.set_page_config(
    page_title=Layout.PAGE_TITLE,
    page_icon=Layout.PAGE_ICON,
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# 🎨 加载自定义 CSS
# ============================================================

def _load_css() -> None:
    """读取 custom.css 并注入页面"""
    css_path = Path(__file__).parent / "styles" / "custom.css"
    if css_path.exists():
        css_text = css_path.read_text(encoding="utf-8")
        st.markdown(f"<style>{css_text}</style>", unsafe_allow_html=True)
    else:
        # 如果 CSS 文件不存在，注入最小暗色主题
        st.markdown("""
        <style>
            html, body, [data-testid="stAppViewContainer"] {
                background-color: #0E1117 !important;
                color: #EAEAEA;
            }
            #MainMenu { visibility: hidden; }
            header[data-testid="stHeader"] { display: none !important; }
            footer { display: none !important; }
        </style>
        """, unsafe_allow_html=True)


_load_css()


# ============================================================
# 📦 Session State 初始化与数据加载
# ============================================================

def _load_data_pipeline(mode: DataMode) -> None:
    """运行 OrchestratorAgent 多智能体管线，获取并加载数据到 session"""
    with st.spinner("正在启动 AI 多智能体协同分析管线，请稍候..."):
        try:
            agent = OrchestratorAgent(mode=mode)
            state = agent.run()
            
            st.session_state[SessionKeys.IPO_DATA] = state.stocks
            st.session_state[SessionKeys.LAST_REFRESH] = state.last_refresh
            st.session_state[SessionKeys.MARKET_BETA] = state.market_condition.market_beta
            st.session_state[SessionKeys.DATA_MODE] = mode.value
            st.session_state["_dashboard_state"] = state
            st.session_state[SessionKeys.DATA_LOADED] = True
            st.session_state[SessionKeys.SELECTED_STOCK] = None
        except Exception as e:
            st.error(f"AI 管线执行失败: {e}")

def _init_session_state() -> None:
    """
    初始化 Session State。
    """
    if not st.session_state.get(SessionKeys.DATA_LOADED, False):
        _load_data_pipeline(DataMode.DEMO)

    # 初始化 UI 状态键（仅在不存在时设置）
    if SessionKeys.SELECTED_STOCK not in st.session_state:
        st.session_state[SessionKeys.SELECTED_STOCK] = None


_init_session_state()


# ============================================================
# 📊 侧边栏
# ============================================================

def _render_sidebar() -> None:
    """渲染侧边栏：数据模式、刷新按钮、大盘状态"""
    with st.sidebar:
        # ---- 品牌标题 ----
        st.markdown("""
        <div style="text-align:center; margin-bottom:1.5rem;">
            <div class="shimmer-text" style="font-size:1.3rem; font-weight:800;">
                🎯 港股打新雷达
            </div>
            <div style="font-size:0.72rem; color:#8B95A5; margin-top:0.25rem;">
                AI 智能推荐看板 v1.0
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")

        # ---- 数据模式选择 ----
        st.markdown(f"<div class='sidebar-title'>⚙️ 数据设置</div>", unsafe_allow_html=True)

        current_mode_str = st.session_state.get(SessionKeys.DATA_MODE, "demo")
        current_index = 0 if current_mode_str == "demo" else 1

        selected_mode_label = st.radio(
            "数据模式",
            options=["Demo（模拟数据）", "Live（实时数据）"],
            index=current_index,
            key="_data_mode_radio_temp",
            label_visibility="collapsed",
        )

        selected_mode = DataMode.DEMO if "Demo" in selected_mode_label else DataMode.LIVE

        # 如果用户切换了模式，立即加载并重绘
        if selected_mode.value != current_mode_str:
            _load_data_pipeline(selected_mode)
            st.rerun()

        # ---- 刷新按钮 ----
        if st.button("🔄 刷新数据", use_container_width=True):
            _load_data_pipeline(selected_mode)
            st.rerun()

        # ---- 上次刷新时间 ----
        last_refresh = st.session_state.get(SessionKeys.LAST_REFRESH)
        if last_refresh:
            st.markdown(f"""
            <div style="font-size:0.72rem; color:{Colors.TEXT_MUTED}; text-align:center; margin-top:0.5rem;">
                上次刷新: {format_refresh_ago(last_refresh)}
            </div>
            """, unsafe_allow_html=True)

        st.markdown("---")

        # ---- 大盘状态 ----
        st.markdown(f"<div class='sidebar-title'>📈 大盘状态</div>", unsafe_allow_html=True)

        dashboard_state: DashboardState = st.session_state.get("_dashboard_state")
        if dashboard_state and dashboard_state.market_condition:
            mc = dashboard_state.market_condition

            # 恒生指数
            if mc.hsi_close:
                hsi_change = mc.hsi_change_5d or 0
                change_color = Colors.GREEN if hsi_change >= 0 else Colors.RED
                change_sign = "+" if hsi_change >= 0 else ""
                st.markdown(f"""
                <div class="sidebar-metric">
                    <span class="sidebar-metric-label">恒生指数</span>
                    <span class="sidebar-metric-value">{mc.hsi_close:,.0f}</span>
                </div>
                <div style="text-align:right; font-size:0.75rem; color:{change_color}; margin-bottom:0.3rem;">
                    近5日 {change_sign}{hsi_change:.1f}%
                </div>
                """, unsafe_allow_html=True)

            # 恒生科技
            if mc.hstech_close:
                st.markdown(f"""
                <div class="sidebar-metric">
                    <span class="sidebar-metric-label">恒生科技</span>
                    <span class="sidebar-metric-value">{mc.hstech_close:,.0f}</span>
                </div>
                """, unsafe_allow_html=True)

            # 趋势判断
            trend_emoji = {"牛市": "🟢", "震荡": "🟡", "熊市": "🔴"}.get(mc.trend.value, "⚪")
            st.markdown(f"""
            <div class="sidebar-metric">
                <span class="sidebar-metric-label">趋势判断</span>
                <span class="sidebar-metric-value">{trend_emoji} {mc.trend.value}</span>
            </div>
            """, unsafe_allow_html=True)

            # MarketBeta
            beta = mc.market_beta
            beta_color = Colors.GREEN if beta >= 1.0 else (Colors.YELLOW if beta >= 0.8 else Colors.RED)
            st.markdown(f"""
            <div class="sidebar-metric">
                <span class="sidebar-metric-label">MarketBeta</span>
                <span class="sidebar-metric-value" style="color:{beta_color};">×{beta:.2f}</span>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("---")

        # ---- 快捷统计 ----
        stocks = st.session_state.get(SessionKeys.IPO_DATA, [])
        st.markdown(f"""
        <div style="text-align:center; font-size:0.75rem; color:{Colors.TEXT_MUTED};">
            共跟踪 <b style="color:{Colors.ACCENT_PURPLE};">{len(stocks)}</b> 只新股
        </div>
        """, unsafe_allow_html=True)


_render_sidebar()


# ============================================================
# 🎯 主区域路由
# ============================================================

def _render_main() -> None:
    """
    主区域路由逻辑：
    - 未选中股票 → 显示雷达主表
    - 选中股票 → 显示详情面板
    """
    selected_code = st.session_state.get(SessionKeys.SELECTED_STOCK)
    stocks = st.session_state.get(SessionKeys.IPO_DATA, [])
    dashboard_state: DashboardState = st.session_state.get("_dashboard_state")

    if selected_code:
        # ---- 详情面板模式 ----
        # 根据代码查找股票
        stock = next((s for s in stocks if s.code == selected_code), None)
        if stock:
            render_detail_panel(stock)
        else:
            st.error(f"未找到股票代码: {selected_code}")
            st.session_state[SessionKeys.SELECTED_STOCK] = None
    else:
        # ---- 雷达主表模式 ----
        # 标题
        st.markdown("""
        <div style="text-align:center; margin-bottom:1.5rem;" class="fade-in">
            <div class="shimmer-text" style="font-size:1.8rem; font-weight:800;">
                🎯 港股打新雷达
            </div>
            <div style="font-size:0.85rem; color:#8B95A5; margin-top:0.3rem;">
                AI 驱动 · 一眼看清每只新股的机会与风险
            </div>
        </div>
        """, unsafe_allow_html=True)

        # KPI 概览
        if dashboard_state:
            render_market_overview(dashboard_state)

        st.markdown("<div style='height:1rem;'></div>", unsafe_allow_html=True)

        # 新股列表
        render_ipo_table(stocks)


_render_main()


# ============================================================
# 📜 底部 Footer
# ============================================================

st.markdown(f"""
<div class="app-footer">
    ⚠️ 数据声明：本看板所有数据仅供参考，不构成任何投资建议。
    Demo 模式下使用虚构数据演示功能。投资有风险，入市需谨慎。<br>
    <span style="color:{Colors.TEXT_MUTED};">
        Built with ❤️ by HK IPO Radar · Powered by Streamlit + Plotly
    </span>
</div>
""", unsafe_allow_html=True)
