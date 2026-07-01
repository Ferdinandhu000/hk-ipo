# -*- coding: utf-8 -*-
"""
示例 / Demo 数据模块

提供 3-4 只模拟新股的完整数据，保证看板在 Demo 模式下随时可运行。
所有数据均为虚构，仅用于演示看板功能。日期相对于「当天」动态生成，
确保倒计时等功能始终有效。
"""

from datetime import date, timedelta, datetime

from data.models import (
    IPOStock,
    CornerstoneInvestor,
    SponsorRecord,
    MarketSentiment,
    MarketCondition,
    MarketTrend,
    AIAnalysis,
    HeatLevel,
    RecommendAction,
    DashboardState,
    DataMode,
)


def _today() -> date:
    """获取当天日期"""
    return date.today()


def generate_sample_stocks() -> list[IPOStock]:
    """
    生成 4 只模拟新股数据。

    日期基于当天动态计算，保证：
    - 2 只正在招股
    - 1 只即将招股
    - 1 只等待上市

    Returns:
        4 只 IPOStock 实例的列表
    """
    today = _today()

    stocks = [
        # ============================================================
        # 🟢 股票 1：星辰 AI 科技 —— AI 赛道热门，各项指标优秀
        # ============================================================
        IPOStock(
            name="星辰 AI 科技",
            code="2899.HK",
            sector="人工智能",
            sector_tag="🤖 AI / 人工智能",
            subscription_start=today - timedelta(days=1),
            subscription_end=today + timedelta(days=2),
            listing_date=today + timedelta(days=7),
            price_low=28.00,
            price_high=32.00,
            lot_size=200,
            entry_fee=6464.36,
            business_summary=(
                "国内领先的大模型基础设施公司，主要为企业客户提供 AI 训练和推理算力平台。"
                "核心产品包括自研 AI 芯片、智算集群调度系统和行业大模型解决方案。"
                "目前已服务超过 200 家头部企业客户，年化收入增速超过 150%。"
            ),
            revenue_ttm=18.5,
            net_profit_ttm=2.3,
            gross_margin=62.0,
            cornerstone_investors=[
                CornerstoneInvestor(name="红杉中国", amount_hkd=3e8, pct=18.0),
                CornerstoneInvestor(name="淡马锡", amount_hkd=2.5e8, pct=15.0),
                CornerstoneInvestor(name="高瓴资本", amount_hkd=2e8, pct=12.0),
                CornerstoneInvestor(name="中东主权基金 ADIA", amount_hkd=1.5e8, pct=9.0),
            ],
            cornerstone_lock_up_months=6,
            sponsors=[
                SponsorRecord(
                    name="中金公司",
                    projects_2yr=38,
                    break_rate_2yr=0.18,
                    avg_return_2yr=15.2,
                ),
                SponsorRecord(
                    name="摩根士丹利",
                    projects_2yr=22,
                    break_rate_2yr=0.15,
                    avg_return_2yr=18.5,
                ),
            ],
            sentiment=MarketSentiment(
                margin_subscription_multiple=220.0,
                retail_heat=HeatLevel.HIGH,
                sentiment_summary="AI 概念持续火爆，机构争抢份额，散户讨论热度极高",
                data_source="综合富途/辉立/耀才数据",
            ),
            ai=AIAnalysis(
                score_fundamental=88,
                score_cornerstone=90,
                score_sponsor=85,
                score_sentiment=95,
                score_pricing=75,
                ai_score=87,
                roi_optimistic=38.0,
                roi_neutral=18.5,
                roi_pessimistic=2.0,
                market_beta_applied=1.0,
                break_probability=0.12,
                recommendation=RecommendAction.FULL_BUY,
                recommendation_text=(
                    "豪华基石阵容（红杉+淡马锡+高瓴+ADIA）合计认购 54%，"
                    "保荐人中金+大摩历史胜率优秀，孖展超 200 倍极度火爆。"
                    "AI 赛道正处风口，建议全力申购。"
                ),
                analysis_summary=(
                    "综合评分 87 分，各维度均表现优异。基石占比 54% 远超平均水平，"
                    "保荐人近两年破发率仅 15%-18%。AI 赛道叠加高孖展倍数，"
                    "首日上涨概率极高。"
                ),
            ),
            data_fetched_at=datetime.now(),
        ),

        # ============================================================
        # 🟡 股票 2：瑞安生物制药 —— 生物医药，指标中等偏上
        # ============================================================
        IPOStock(
            name="瑞安生物制药",
            code="6155.HK",
            sector="生物医药",
            sector_tag="💊 生物医药",
            subscription_start=today - timedelta(days=2),
            subscription_end=today + timedelta(days=1),
            listing_date=today + timedelta(days=6),
            price_low=15.50,
            price_high=18.20,
            lot_size=500,
            entry_fee=9191.00,
            business_summary=(
                "专注于自身免疫疾病的创新药企，核心管线 RA-201（JAK 抑制剂）已完成"
                "三期临床试验，预计明年获批上市。另有 3 条二期管线覆盖银屑病与系统性红斑狼疮。"
                "公司尚未盈利，但在研管线价值被市场看好。"
            ),
            revenue_ttm=1.2,
            net_profit_ttm=-3.8,
            gross_margin=78.0,
            cornerstone_investors=[
                CornerstoneInvestor(name="Hillhouse Capital", amount_hkd=1.5e8, pct=15.0),
                CornerstoneInvestor(name="OrbiMed", amount_hkd=1.2e8, pct=12.0),
                CornerstoneInvestor(name="国药资本", amount_hkd=8e7, pct=8.0),
            ],
            cornerstone_lock_up_months=6,
            sponsors=[
                SponsorRecord(
                    name="华泰国际",
                    projects_2yr=28,
                    break_rate_2yr=0.28,
                    avg_return_2yr=8.3,
                ),
            ],
            sentiment=MarketSentiment(
                margin_subscription_multiple=45.0,
                retail_heat=HeatLevel.MEDIUM,
                sentiment_summary="生物医药板块回暖，管线数据受关注，但尚未盈利令部分散户犹豫",
                data_source="综合富途/辉立数据",
            ),
            ai=AIAnalysis(
                score_fundamental=62,
                score_cornerstone=70,
                score_sponsor=60,
                score_sentiment=65,
                score_pricing=58,
                ai_score=63,
                roi_optimistic=22.0,
                roi_neutral=6.5,
                roi_pessimistic=-8.0,
                market_beta_applied=1.0,
                break_probability=0.35,
                recommendation=RecommendAction.ONE_LOT,
                recommendation_text=(
                    "基石阵容尚可（Hillhouse + OrbiMed + 国药）合计 35%，"
                    "保荐人华泰国际近两年破发率 28% 处于中等水平。"
                    "公司尚未盈利是最大风险点，建议仅用现金申购一手试水。"
                ),
                analysis_summary=(
                    "综合评分 63 分。生物医药创新药赛道有想象力，但未盈利企业"
                    "波动性较大。孖展 45 倍属于中等热度，保荐人历史表现一般。"
                ),
            ),
            data_fetched_at=datetime.now(),
        ),

        # ============================================================
        # 🔴 股票 3：鼎盛地产集团 —— 传统地产，各项指标偏弱
        # ============================================================
        IPOStock(
            name="鼎盛地产集团",
            code="3488.HK",
            sector="地产建筑",
            sector_tag="🏗️ 地产建筑",
            subscription_start=today,
            subscription_end=today + timedelta(days=3),
            listing_date=today + timedelta(days=8),
            price_low=3.20,
            price_high=4.00,
            lot_size=1000,
            entry_fee=4040.40,
            business_summary=(
                "华南地区中型房地产开发商，主要在二三线城市开发住宅项目。"
                "2025 年营收约 80 亿港元，净利润率约 5%。"
                "行业整体处于去杠杆周期，公司负债率偏高。"
            ),
            revenue_ttm=80.0,
            net_profit_ttm=4.0,
            gross_margin=18.0,
            cornerstone_investors=[
                CornerstoneInvestor(name="某地方国资", amount_hkd=5e7, pct=8.0),
            ],
            cornerstone_lock_up_months=6,
            sponsors=[
                SponsorRecord(
                    name="招银国际",
                    projects_2yr=32,
                    break_rate_2yr=0.38,
                    avg_return_2yr=-2.1,
                ),
            ],
            sentiment=MarketSentiment(
                margin_subscription_multiple=5.0,
                retail_heat=HeatLevel.LOW,
                sentiment_summary="地产板块持续低迷，散户兴趣寡淡，关注度极低",
                data_source="综合富途数据",
            ),
            ai=AIAnalysis(
                score_fundamental=30,
                score_cornerstone=20,
                score_sponsor=35,
                score_sentiment=15,
                score_pricing=40,
                ai_score=28,
                roi_optimistic=5.0,
                roi_neutral=-8.0,
                roi_pessimistic=-22.0,
                market_beta_applied=1.0,
                break_probability=0.72,
                recommendation=RecommendAction.SKIP,
                recommendation_text=(
                    "基石仅有一家地方国资认购 8%，保荐人招银近两年破发率高达 38%。"
                    "地产赛道当前极度不受资金青睐，孖展仅 5 倍几乎无热度。"
                    "破发概率超过 70%，强烈建议放弃。"
                ),
                analysis_summary=(
                    "综合评分 28 分。地产行业逆风，基石占比极低，保荐人历史战绩不佳，"
                    "市场情绪冰冷。首日破发可能性极大。"
                ),
            ),
            data_fetched_at=datetime.now(),
        ),

        # ============================================================
        # 📋 股票 4：天际智能汽车 —— 即将招股，新能源汽车赛道
        # ============================================================
        IPOStock(
            name="天际智能汽车",
            code="1797.HK",
            sector="智能汽车",
            sector_tag="🚗 智能汽车",
            subscription_start=today + timedelta(days=2),
            subscription_end=today + timedelta(days=5),
            listing_date=today + timedelta(days=10),
            price_low=42.00,
            price_high=50.00,
            lot_size=100,
            entry_fee=5050.50,
            business_summary=(
                "新兴智能电动汽车品牌，主打 20-35 万价位区间的中高端 SUV 市场。"
                "2025 年全年交付约 8 万辆，同比增长 210%。"
                "核心竞争力为自研智驾系统和城市 NOA 能力，已获得多个城市的无图智驾许可。"
            ),
            revenue_ttm=120.0,
            net_profit_ttm=-15.0,
            gross_margin=12.0,
            cornerstone_investors=[
                CornerstoneInvestor(name="小米集团", amount_hkd=5e8, pct=20.0),
                CornerstoneInvestor(name="宁德时代", amount_hkd=3e8, pct=12.0),
                CornerstoneInvestor(name="Abu Dhabi Investment Authority", amount_hkd=2e8, pct=8.0),
            ],
            cornerstone_lock_up_months=6,
            sponsors=[
                SponsorRecord(
                    name="中信证券",
                    projects_2yr=35,
                    break_rate_2yr=0.22,
                    avg_return_2yr=12.0,
                ),
                SponsorRecord(
                    name="高盛",
                    projects_2yr=18,
                    break_rate_2yr=0.12,
                    avg_return_2yr=22.5,
                ),
            ],
            sentiment=MarketSentiment(
                margin_subscription_multiple=None,  # 尚未开始招股，暂无数据
                retail_heat=HeatLevel.HIGH,
                sentiment_summary="智能汽车赛道受热捧，小米+宁德背书引爆话题，散户翘首以盼",
                data_source="社区舆情综合分析",
            ),
            ai=AIAnalysis(
                score_fundamental=72,
                score_cornerstone=82,
                score_sponsor=80,
                score_sentiment=88,
                score_pricing=65,
                ai_score=78,
                roi_optimistic=32.0,
                roi_neutral=14.0,
                roi_pessimistic=-3.0,
                market_beta_applied=1.0,
                break_probability=0.20,
                recommendation=RecommendAction.FULL_BUY,
                recommendation_text=(
                    "小米 + 宁德时代 + ADIA 的基石阵容极具号召力，合计 40%。"
                    "保荐人中信 + 高盛组合历史胜率优秀。虽然公司尚未盈利，但交付量增速惊人。"
                    "智能汽车赛道正在风口，建议全力申购。"
                ),
                analysis_summary=(
                    "综合评分 78 分。产业资本（小米+宁德时代）深度参与背书，"
                    "交付量高增长打消部分盈利担忧。保荐人阵容豪华，市场期待度高。"
                ),
            ),
            data_fetched_at=datetime.now(),
        ),
    ]

    return stocks


def generate_sample_market_condition() -> MarketCondition:
    """
    生成模拟的大盘状态数据。

    Returns:
        MarketCondition 实例，默认为中性市场（beta=1.0）
    """
    return MarketCondition(
        hsi_close=19850.0,
        hstech_close=4520.0,
        hsi_change_5d=-1.2,
        hsi_change_20d=3.5,
        trend=MarketTrend.NEUTRAL,
        market_beta=1.0,
        snapshot_date=date.today(),
    )


def generate_sample_dashboard_state() -> DashboardState:
    """
    生成完整的看板 Demo 状态数据。

    Returns:
        DashboardState 实例，包含 4 只模拟新股和大盘状态
    """
    return DashboardState(
        stocks=generate_sample_stocks(),
        market_condition=generate_sample_market_condition(),
        data_mode=DataMode.DEMO,
        last_refresh=datetime.now(),
    )
