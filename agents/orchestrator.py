# -*- coding: utf-8 -*-
"""
总指挥 Agent (Orchestrator Agent)

职责：
    编排并调度港股打新看板的所有子 Agent 管线：
    1. 调度 IPOScannerAgent 扫描新股
    2. 调度 FundamentalsAgent 补充基本面
    3. 调度 CornerstoneAgent 补充基石投资者
    4. 调度 SponsorAgent 补充保荐人历史战绩
    5. 调度 SentimentAgent 获取市场情绪与大盘状态
    6. 调度 QuantAgent 执行最终的量化评分与 ROI 预测
    7. 汇总所有数据，返回 DashboardState 对象

工作模式：
    - Demo 模式：使用模拟数据驱动，通过子 Agent 传递并由 QuantAgent 真实计算评分
    - Live 模式：调用实时采集接口（当前为 stub，抛出 NotImplementedError）
"""

from __future__ import annotations

import sys
from datetime import datetime

# ---- Windows GBK 编码问题修复 (处理 emoji 打印) ----
if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

from data.models import DataMode, DashboardState, MarketCondition
from agents.ipo_scanner import IPOScannerAgent
from agents.fundamentals import FundamentalsAgent
from agents.cornerstone import CornerstoneAgent
from agents.sponsor import SponsorAgent
from agents.sentiment import SentimentAgent
from agents.quant import QuantAgent


class OrchestratorAgent:
    """
    总指挥 Agent
    
    负责串联和调度整个多智能体分析管线。
    """

    def __init__(self, mode: DataMode = DataMode.DEMO):
        """
        初始化总指挥 Agent。

        Args:
            mode: 数据模式（demo / live）
        """
        self.mode = mode
        self.scanner = IPOScannerAgent(mode=self.mode)
        self.fundamentals = FundamentalsAgent(mode=self.mode)
        self.cornerstone = CornerstoneAgent(mode=self.mode)
        self.sponsor = SponsorAgent(mode=self.mode)
        self.sentiment = SentimentAgent(mode=self.mode)

    def run(self) -> DashboardState:
        """
        执行完整的智能体协同管线，汇总数据并返回 DashboardState。

        Returns:
            DashboardState: 看板所需的全局结构化数据
        """
        print(f"[Orchestrator] 启动分析管线，模式：{self.mode.value}")

        # 1. 扫描新股基础列表
        stocks = self.scanner.run()

        # 2. 补全基本面数据
        stocks = self.fundamentals.run(stocks)

        # 3. 补全基石投资者数据
        stocks = self.cornerstone.run(stocks)

        # 4. 补全保荐人历史数据
        stocks = self.sponsor.run(stocks)

        # 5. 获取市场情绪和大盘状态
        stocks, market_condition = self.sentiment.run(stocks)

        # 6. 调度最核心的量化 Agent 重新计算 AI 评分、破发率和 ROI
        quant = QuantAgent(market_condition=market_condition)
        scored_stocks = quant.run(stocks)

        # 7. 汇总为看板全局状态
        state = DashboardState(
            stocks=scored_stocks,
            market_condition=market_condition,
            data_mode=self.mode,
            last_refresh=datetime.now(),
        )

        print("[Orchestrator] 分析管线执行完毕，成功生成看板状态")
        return state
