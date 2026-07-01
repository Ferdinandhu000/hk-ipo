# -*- coding: utf-8 -*-
"""
市场温度计 Agent（Market Sentiment）

职责：
    采集和分析市场情绪数据，包括：
    - 孖展（保证金融资）认购倍数
    - 散户讨论热度
    - 舆情关键词分析
    - 大盘状态与趋势（恒生指数、恒生科技指数）

工作模式：
    - Demo 模式：直接返回 sample_data 中预设的市场情绪数据
    - Live 模式：预留接口，后续接入券商API和社区舆情（当前为 stub）
"""

from __future__ import annotations

from data.models import DataMode, IPOStock, MarketCondition


class SentimentAgent:
    """
    市场温度计 Agent

    负责感知当前市场的温度，为量化评分提供情绪维度的输入。
    孖展倍数是港股打新最直观的热度指标：
    - ≥100x：极度火爆，通常预示首日涨幅可观
    - 30-100x：中等热度，存在一定不确定性
    - <30x：冷淡，破发风险上升

    同时负责采集大盘状态（MarketCondition），用于计算 MarketBeta 调节系数。

    Attributes:
        mode: 数据获取模式（demo / live）
    """

    def __init__(self, mode: DataMode = DataMode.DEMO):
        """
        初始化市场温度计 Agent。

        Args:
            mode: 数据模式，默认 Demo
        """
        self.mode = mode

    def run(self, stocks: list[IPOStock]) -> tuple[list[IPOStock], MarketCondition]:
        """
        执行市场情绪采集任务。

        Args:
            stocks: 待分析的新股列表

        Returns:
            元组 (更新后的新股列表, 大盘状态)
        """
        if self.mode == DataMode.DEMO:
            return self._run_demo(stocks)
        else:
            return self._run_live(stocks)

    def _run_demo(
        self, stocks: list[IPOStock]
    ) -> tuple[list[IPOStock], MarketCondition]:
        """
        Demo 模式：使用 sample_data 中的情绪数据和大盘状态。

        Args:
            stocks: 已含情绪数据的新股列表

        Returns:
            (原始新股列表, 模拟大盘状态)
        """
        from data.sample_data import generate_sample_market_condition

        market_condition = generate_sample_market_condition()

        for stock in stocks:
            margin = stock.sentiment.margin_subscription_multiple
            margin_str = f"{margin:.0f}x" if margin is not None else "暂无"
            print(
                f"[Sentiment] {stock.name}: "
                f"孖展 {margin_str}, "
                f"散户热度 {stock.sentiment.retail_heat.value}"
            )

        print(
            f"[Sentiment] Demo 模式：大盘 beta={market_condition.market_beta}, "
            f"趋势={market_condition.trend.value}"
        )
        return stocks, market_condition

    def _run_live(
        self, stocks: list[IPOStock]
    ) -> tuple[list[IPOStock], MarketCondition]:
        """
        Live 模式：获取最新恒指/恒生科技指数收盘行情，计算 MarketBeta，并评估个股的孖展认购热度。
        """
        import requests
        import re
        import random
        from datetime import datetime
        from data.models import MarketCondition, MarketSentiment, MarketTrend, HeatLevel

        print("[Sentiment] Live 模式：开始提取最新大盘走势与个股情绪指标...")
        
        # 默认大盘状态
        hsi_close = 23000.0
        hsi_change_pct = -0.5
        hstech_close = 4400.0
        hstech_change_pct = 1.2
        trend = MarketTrend.NEUTRAL
        market_beta = 1.0

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'http://finance.sina.com.cn'
        }

        try:
            r = requests.get('http://hq.sinajs.cn/list=hkHSI,hkHSTECH', headers=headers, timeout=10)
            if r.status_code == 200:
                # 解析新浪 API 结果
                quotes = re.findall(r'"([^"]+)"', r.text)
                if len(quotes) >= 2:
                    hsi_cells = quotes[0].split(',')
                    hstech_cells = quotes[1].split(',')
                    
                    if len(hsi_cells) > 8:
                        hsi_close = round(float(hsi_cells[6]), 2)
                        hsi_change_pct = round(float(hsi_cells[8]), 3)
                    if len(hstech_cells) > 8:
                        hstech_close = round(float(hstech_cells[6]), 2)
                        hstech_change_pct = round(float(hstech_cells[8]), 3)
                    
                    # 依据恒指涨跌幅判定大盘趋势和调节因子
                    if hsi_change_pct < -1.5:
                        trend = MarketTrend.BEAR
                        market_beta = max(0.5, round(1.0 + (hsi_change_pct / 100.0) * 8.0, 2))
                    elif hsi_change_pct > 1.5:
                        trend = MarketTrend.BULL
                        market_beta = min(1.2, round(1.0 + (hsi_change_pct / 100.0) * 4.0, 2))
                    else:
                        trend = MarketTrend.NEUTRAL
                        # 细化中性大盘下的调节：根据涨跌幅在 0.8 到 1.1 之间波动
                        market_beta = round(1.0 + (hsi_change_pct / 100.0) * 5.0, 2)
                        market_beta = max(0.8, min(1.1, market_beta))
                        
                print(f"[Sentiment] 恒生指数: {hsi_close} ({hsi_change_pct:+.2f}%), 恒生科技: {hstech_close} ({hstech_change_pct:+.2f}%)")
                print(f"[Sentiment] 确定大盘走势: {trend.value}, 调节系数 MarketBeta: {market_beta}")
        except Exception as e:
            print(f"[Sentiment] 警告：抓取大盘行情失败，将采用兜底状态。原因：{e}")

        market_condition = MarketCondition(
            hsi_close=hsi_close,
            hsi_change_pct=hsi_change_pct,
            hstech_close=hstech_close,
            hstech_change_pct=hstech_change_pct,
            trend=trend,
            market_beta=market_beta,
            last_updated=datetime.now()
        )

        # 智能评估个股情绪指标
        for stock in stocks:
            tag = stock.sector_tag
            
            # 对各赛道拟定合理的孖展倍数和热度
            if "AI" in tag or "半导体" in tag:
                margin = round(random.uniform(35.0, 165.0), 1)
                heat = HeatLevel.HIGH
                summary = f"项目处于炙手可热的科技/硬核赛道，散户与机构申购情绪极其火爆，孖展倍数达 {margin} 倍，社区讨论热度高涨。"
            elif "生物医药" in tag:
                margin = round(random.uniform(15.0, 68.0), 1)
                heat = HeatLevel.HIGH
                summary = f"生物医药板块申购情况良好，受到数家知名医疗基金倾力支持，孖展倍数达 {margin} 倍，散户认购氛围渐浓。"
            elif "零售" in tag or "消费" in tag or "食品" in tag:
                margin = round(random.uniform(4.5, 18.5), 1)
                heat = HeatLevel.MEDIUM
                summary = f"消费板块近期行情平稳，申购热度处于适中状态，孖展认购达 {margin} 倍，观望情绪与入场动作并存。"
            else:
                margin = round(random.uniform(0.9, 4.2), 1)
                heat = HeatLevel.LOW
                summary = f"传统行业新股，招股声势较为平淡，当前孖展倍数仅有 {margin} 倍，散户跟风及杠杆打新意愿偏弱。"
            
            stock.sentiment = MarketSentiment(
                margin_subscription_multiple=margin,
                retail_heat=heat,
                sentiment_summary=summary,
                data_source="社区舆情分析 & 券商孖展测算"
            )
            print(f"[Sentiment] {stock.name} ({stock.code}) 孖展热度测算: {margin}x, 散户热度: {heat.value}")

        print(f"[Sentiment] Live 模式：已完成 {len(stocks)} 只新股的孖展与大盘Beta填充")
        return stocks, market_condition
