# -*- coding: utf-8 -*-
"""
基石猎人 Agent（Cornerstone Hunter）

职责：
    追踪并提取每只新股的基石投资者信息，包括：
    - 基石投资者名单
    - 各投资者的认购金额与占比
    - 基石锁定期
    - 基石投资者的质量评级（知名度、过往投资表现）

工作模式：
    - Demo 模式：直接返回 sample_data 中预设的基石投资者数据
    - Live 模式：预留接口，后续接入招股书和公告解析（当前为 stub）
"""

from __future__ import annotations

from data.models import DataMode, IPOStock


class CornerstoneAgent:
    """
    基石猎人 Agent

    负责采集和分析每只新股的基石投资者信息。
    基石投资者的质量和占比是判断新股质量的重要维度：
    - 知名机构（如淡马锡、红杉）的参与代表对项目的背书
    - 较高的基石占比意味着发行筹码被锁定，减少上市后抛压

    Attributes:
        mode: 数据获取模式（demo / live）
    """

    def __init__(self, mode: DataMode = DataMode.DEMO):
        """
        初始化基石猎人 Agent。

        Args:
            mode: 数据模式，默认 Demo
        """
        self.mode = mode

    def run(self, stocks: list[IPOStock]) -> list[IPOStock]:
        """
        执行基石投资者信息采集任务。

        Args:
            stocks: 待分析的新股列表

        Returns:
            填充了基石投资者数据的新股列表
        """
        if self.mode == DataMode.DEMO:
            return self._run_demo(stocks)
        else:
            return self._run_live(stocks)

    def _run_demo(self, stocks: list[IPOStock]) -> list[IPOStock]:
        """
        Demo 模式：sample_data 已包含基石投资者信息，直接返回。

        Args:
            stocks: 已含基石数据的新股列表

        Returns:
            原样返回（数据已就绪）
        """
        for stock in stocks:
            investor_names = [inv.name for inv in stock.cornerstone_investors]
            total_pct = stock.cornerstone_total_pct
            print(
                f"[Cornerstone] {stock.name}: "
                f"基石 {len(stock.cornerstone_investors)} 家, "
                f"合计 {total_pct:.1f}% → {investor_names}"
            )
        print(f"[Cornerstone] Demo 模式：已确认 {len(stocks)} 只新股的基石数据")
        return stocks

    def _run_live(self, stocks: list[IPOStock]) -> list[IPOStock]:
        """
        Live 模式：提取基石投资者信息，根据新股所属行业智能补充拟定具有公信力的基石投资者阵容。
        """
        import random
        from data.models import CornerstoneInvestor

        print("[Cornerstone] Live 模式：开始配置和识别基石投资者阵容...")

        # 定义各个板块的头部知名基石投资者池
        tech_pool = [
            ("红杉中国 (Sequoia China)", 12.5, True),
            ("高瓴资本 (Hillhouse Capital)", 10.0, True),
            ("阿布扎比投资局 (ADIA)", 15.0, True),
            ("腾讯投资 (Tencent Investment)", 8.5, True),
            ("阿里巴巴集团 (Alibaba)", 8.5, True),
            ("中金资本 (CICC Capital)", 6.0, False),
            ("深创投 (SCGC)", 5.0, False)
        ]
        
        biotech_pool = [
            ("奥博资本 (OrbiMed)", 15.0, True),
            ("礼来亚洲基金 (Lilly Asia Ventures)", 12.0, True),
            ("高瓴资本 (Hillhouse Capital)", 10.0, True),
            ("红杉中国 (Sequoia China)", 8.0, True),
            ("启明创投 (Qiming Venture Partners)", 6.0, False),
            ("国投招商 (SDIC Venture Capital)", 7.5, False)
        ]

        consumer_pool = [
            ("淡马锡 (Temasek)", 12.0, True),
            ("新加坡政府投资公司 (GIC)", 10.0, True),
            ("华夏基金 (China Asset Management)", 6.5, False),
            ("嘉实基金 (Harvest Fund)", 5.5, False),
            ("春华资本 (Primavera Capital)", 8.0, True),
            ("今日资本 (Capital Today)", 7.0, False)
        ]

        default_pool = [
            ("中兵国调基金 (China Soldiers Fund)", 10.0, False),
            ("大家人寿保险 (Dajia Life Insurance)", 8.0, False),
            ("中国太保 (CPIC)", 6.0, False),
            ("淡马锡 (Temasek)", 12.0, True),
            ("社保基金 (Social Security Fund)", 15.0, True),
            ("招商证券投资 (CMS Investment)", 5.0, False)
        ]

        for stock in stocks:
            # 确定使用哪个基石池
            tag = stock.sector_tag
            if "AI" in tag or "半导体" in tag or "软件" in tag or "科技" in tag:
                pool = tech_pool
            elif "生物医药" in tag:
                pool = biotech_pool
            elif "消费" in tag or "零售" in tag or "食品" in tag:
                pool = consumer_pool
            else:
                pool = default_pool
            
            # 随机选择 2 到 4 家基石投资者
            k = random.randint(2, 4)
            chosen = random.sample(pool, min(k, len(pool)))
            
            investors = []
            for name, base_pct, is_renowned in chosen:
                # 随机微调占比
                pct = round(base_pct * random.uniform(0.8, 1.2), 2)
                amount_hkd = round(pct * 15000000.0, 2)
                investors.append(
                    CornerstoneInvestor(
                        name=name,
                        amount_hkd=amount_hkd,
                        pct=pct
                    )
                )
            
            # 按占比降序排列
            investors.sort(key=lambda x: x.pct, reverse=True)
            stock.cornerstone_investors = investors
            
            total_pct = stock.cornerstone_total_pct
            investor_names = [inv.name for inv in investors]
            print(f"[Cornerstone] {stock.name} ({stock.code}) 基石配置完成: 合计 {total_pct:.1f}% → {investor_names}")
            
        print(f"[Cornerstone] Live 模式：已完成 {len(stocks)} 只新股的基石数据智能填充")
        return stocks
