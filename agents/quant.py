# -*- coding: utf-8 -*-
"""
量化策略师 Agent（Quant Strategist）⚠️ 核心 Agent

职责：
    基于多维度数据对每只新股进行量化评分和 ROI 预测，包括：
    - 基本面得分（25%）：毛利率、盈利状况、赛道热度
    - 基石得分（20%）：基石投资者总占比
    - 保荐人得分（20%）：近两年破发率
    - 市场情绪得分（20%）：孖展认购倍数
    - 定价得分（15%）：基于市盈率合理性
    - 综合 AI 评分 = 加权求和
    - ROI 预测 = 多因子回归 × MarketBeta 大盘调节
    - 破发概率 = 修正公式
    - 行动建议 = 基于分数和破发概率映射

关键算法：
    1. 评分模型：五维加权评分体系，权重来自 config.ScoreWeights
    2. ROI 预测：ROI_neutral = α·Corner + β·Sponsor + γ·Sentiment + δ·Fundamental - PricingPenalty
    3. 大盘调节：ROI_final = ROI_base × market_beta
    4. 情景分析：乐观 = neutral × 1.8, 悲观 = neutral × 0.3 - 5%
    5. 破发概率：基于 ai_score 的修正公式
    6. 行动映射：≥75分且破发<25% → 全力申购, 50-74分 → 一手摸, <50分 → 放弃
"""

from __future__ import annotations

from data.models import (
    AIAnalysis,
    IPOStock,
    MarketCondition,
    RecommendAction,
)
from config import ScoreWeights, RecommendationLevel


class QuantAgent:
    """
    量化策略师 Agent（核心评分引擎）

    这是整个 Agent 管线中最核心的模块，负责将各维度的原始数据
    转化为可操作的投资建议。所有评分逻辑均为真实计算，不依赖硬编码。

    评分体系：
        - 基本面 (25%)：综合毛利率、盈利能力、赛道热度
        - 基石 (20%)：基石投资者总占比，≥50% 满分
        - 保荐人 (20%)：近两年破发率，≤20% 满分
        - 市场情绪 (20%)：孖展倍数，≥100x 满分
        - 定价 (15%)：基于市盈率合理性

    Attributes:
        market_condition: 大盘状态，提供 MarketBeta 调节系数
    """

    def __init__(self, market_condition: MarketCondition | None = None):
        """
        初始化量化策略师 Agent。

        Args:
            market_condition: 大盘状态，为 None 时使用默认 beta=1.0
        """
        self.market_condition = market_condition or MarketCondition()

    # ================================================================
    # 公共接口
    # ================================================================

    def run(self, stocks: list[IPOStock]) -> list[IPOStock]:
        """
        对所有新股执行量化评分和 ROI 预测。

        遍历每只新股，依次计算五维分数、综合评分、ROI 预测、
        破发概率和行动建议，最终将结果写入 IPOStock.ai 字段。

        Args:
            stocks: 已填充基础信息和各维度数据的新股列表

        Returns:
            更新了 AI 分析结果的新股列表
        """
        market_beta = self.market_condition.market_beta
        print(f"[Quant] 开始量化评分，大盘 beta={market_beta:.2f}")

        scored_stocks = []
        for stock in stocks:
            analysis = self._score_stock(stock, market_beta)
            # 使用 model_copy 更新 ai 字段（Pydantic v2 推荐方式）
            updated = stock.model_copy(update={"ai": analysis})
            scored_stocks.append(updated)
            print(
                f"[Quant] {stock.name}: "
                f"AI={analysis.ai_score:.1f} "
                f"ROI=[{analysis.roi_pessimistic:+.1f}%, "
                f"{analysis.roi_neutral:+.1f}%, "
                f"{analysis.roi_optimistic:+.1f}%] "
                f"破发={analysis.break_probability:.0%} "
                f"→ {analysis.recommendation.value}"
            )

        print(f"[Quant] 评分完成，共处理 {len(scored_stocks)} 只新股")
        return scored_stocks

    # ================================================================
    # 核心评分逻辑
    # ================================================================

    def _score_stock(self, stock: IPOStock, market_beta: float) -> AIAnalysis:
        """
        对单只新股执行完整的量化评分流程。

        Args:
            stock: 待评分的新股
            market_beta: 大盘调节系数

        Returns:
            AIAnalysis 实例，包含所有评分和预测结果
        """
        # 第一步：计算各维度分项得分（0-100）
        score_fundamental = self._calc_fundamental_score(stock)
        score_cornerstone = self._calc_cornerstone_score(stock)
        score_sponsor = self._calc_sponsor_score(stock)
        score_sentiment = self._calc_sentiment_score(stock)
        score_pricing = self._calc_pricing_score(stock)

        # 第二步：加权求和 → AI 综合评分
        ai_score = (
            score_fundamental * ScoreWeights.FUNDAMENTAL
            + score_cornerstone * ScoreWeights.CORNERSTONE
            + score_sponsor * ScoreWeights.SPONSOR
            + score_sentiment * ScoreWeights.SENTIMENT
            + score_pricing * ScoreWeights.PRICING
        )

        # 第三步：ROI 预测
        roi_neutral, roi_optimistic, roi_pessimistic = self._calc_roi(
            score_fundamental=score_fundamental,
            score_cornerstone=score_cornerstone,
            score_sponsor=score_sponsor,
            score_sentiment=score_sentiment,
            score_pricing=score_pricing,
            market_beta=market_beta,
        )

        # 第四步：破发概率
        break_probability = self._calc_break_probability(ai_score)

        # 第五步：行动建议
        recommendation = self._map_recommendation(ai_score, break_probability)

        # 第六步：生成分析文本
        recommendation_text = self._generate_recommendation_text(
            stock, ai_score, break_probability, recommendation
        )
        analysis_summary = self._generate_analysis_summary(
            stock, ai_score, score_fundamental, score_cornerstone,
            score_sponsor, score_sentiment, score_pricing,
            roi_neutral, break_probability
        )

        return AIAnalysis(
            score_fundamental=round(score_fundamental, 1),
            score_cornerstone=round(score_cornerstone, 1),
            score_sponsor=round(score_sponsor, 1),
            score_sentiment=round(score_sentiment, 1),
            score_pricing=round(score_pricing, 1),
            ai_score=round(ai_score, 1),
            roi_optimistic=round(roi_optimistic, 1),
            roi_neutral=round(roi_neutral, 1),
            roi_pessimistic=round(roi_pessimistic, 1),
            market_beta_applied=market_beta,
            break_probability=round(break_probability, 4),
            recommendation=recommendation,
            recommendation_text=recommendation_text,
            analysis_summary=analysis_summary,
        )

    # ================================================================
    # 各维度评分函数
    # ================================================================

    def _calc_fundamental_score(self, stock: IPOStock) -> float:
        """
        计算基本面得分（0-100），权重 25%。

        评估维度：
        1. 毛利率贡献（40%）：毛利率映射到 0-100
        2. 盈利状况贡献（30%）：已盈利加分，亏损减分
        3. 赛道热度贡献（30%）：热门赛道加分

        Args:
            stock: 待评分的新股

        Returns:
            基本面得分（0-100）
        """
        score = 0.0

        # --- 毛利率贡献（40 分满分）---
        # 毛利率 ≥60% → 40 分, 线性递减到 0% → 0 分
        gm = stock.gross_margin or 0.0
        gm_score = min(gm / 60.0, 1.0) * 40.0
        score += gm_score

        # --- 盈利状况贡献（30 分满分）---
        if stock.net_profit_ttm is not None and stock.net_profit_ttm > 0:
            # 已盈利：利润越高得分越高，最高 30 分
            # 净利润 ≥5 亿满分，线性递减
            profit_score = min(stock.net_profit_ttm / 5.0, 1.0) * 30.0
            score += profit_score
        elif stock.net_profit_ttm is not None and stock.net_profit_ttm <= 0:
            # 未盈利企业：基础 5 分（不完全否定未盈利的创新药/科技股）
            # 但如果收入增速高（通过收入规模间接反映），可以额外加分
            base = 5.0
            if stock.revenue_ttm and stock.revenue_ttm > 10:
                # 收入超过 10 亿的未盈利企业，可能处于高增长期
                base += min(stock.revenue_ttm / 50.0, 1.0) * 10.0
            score += base
        else:
            # 无数据：给中间分
            score += 15.0

        # --- 赛道热度贡献（30 分满分）---
        hot_sectors = {"人工智能", "AI", "半导体", "智能汽车", "新能源"}
        warm_sectors = {"生物医药", "软件科技", "游戏娱乐", "先进制造"}
        cold_sectors = {"地产建筑", "金融服务", "物流供应链"}

        sector = stock.sector
        if any(hot in sector for hot in hot_sectors):
            score += 30.0  # 热门赛道满分
        elif any(warm in sector for warm in warm_sectors):
            score += 20.0  # 温和赛道
        elif any(cold in sector for cold in cold_sectors):
            score += 8.0   # 冷门赛道
        else:
            score += 15.0  # 其他赛道，中间分

        return min(score, 100.0)

    def _calc_cornerstone_score(self, stock: IPOStock) -> float:
        """
        计算基石投资者得分（0-100），权重 20%。

        规则：
        - 基石总占比 ≥50% → 满分 100
        - 线性递减：score = (总占比 / 50) × 100
        - 无基石投资者 → 0 分

        Args:
            stock: 待评分的新股

        Returns:
            基石得分（0-100）
        """
        total_pct = stock.cornerstone_total_pct  # 已通过 computed_field 计算
        if total_pct <= 0:
            return 0.0
        # 线性映射：50% → 100 分
        score = (total_pct / 50.0) * 100.0
        return min(score, 100.0)

    def _calc_sponsor_score(self, stock: IPOStock) -> float:
        """
        计算保荐人得分（0-100），权重 20%。

        规则：
        - 取所有保荐人中最低破发率进行评分（取最优表现）
        - 破发率 ≤20% → 满分 100
        - 线性递减：score = max(0, (1 - break_rate / 0.5)) × 100
          即破发率 50% 时为 0 分
        - 无保荐人数据 → 30 分（给予基础分）

        Args:
            stock: 待评分的新股

        Returns:
            保荐人得分（0-100）
        """
        if not stock.sponsors:
            return 30.0  # 无保荐人数据，给基础分

        # 取最低破发率（最优保荐人）
        best_break_rate = min(sp.break_rate_2yr for sp in stock.sponsors)

        if best_break_rate <= 0.20:
            # 破发率 ≤20%：满分 100
            return 100.0
        elif best_break_rate >= 0.50:
            # 破发率 ≥50%：最低分 0
            return 0.0
        else:
            # 20%-50% 之间线性递减
            # 在 0.20 时为 100, 在 0.50 时为 0
            score = (1.0 - (best_break_rate - 0.20) / 0.30) * 100.0
            return max(score, 0.0)

    def _calc_sentiment_score(self, stock: IPOStock) -> float:
        """
        计算市场情绪得分（0-100），权重 20%。

        规则：
        - 孖展倍数 ≥100x → 满分 100
        - 线性递减：score = (倍数 / 100) × 100
        - 无孖展数据 → 基于散户热度给出估计分

        Args:
            stock: 待评分的新股

        Returns:
            市场情绪得分（0-100）
        """
        margin_mult = stock.sentiment.margin_subscription_multiple

        if margin_mult is not None:
            # 有孖展数据：线性映射，100x → 100 分
            score = (margin_mult / 100.0) * 100.0
            return min(score, 100.0)
        else:
            # 无孖展数据（通常是尚未开始招股的新股）
            # 根据散户热度给出估计分
            from data.models import HeatLevel
            heat_scores = {
                HeatLevel.HIGH: 70.0,   # 高热度假定 70 分
                HeatLevel.MEDIUM: 45.0, # 中热度假定 45 分
                HeatLevel.LOW: 20.0,    # 低热度假定 20 分
            }
            return heat_scores.get(stock.sentiment.retail_heat, 45.0)

    def _calc_pricing_score(self, stock: IPOStock) -> float:
        """
        计算定价合理性得分（0-100），权重 15%。

        基于隐含市盈率（P/E）评估定价是否合理：
        - P/E 在 10-25 之间为理想区间 → 高分
        - P/E 过高（>50）或为负（亏损企业）→ 扣分
        - 无法计算 P/E 时，基于毛利率和赛道给出估计

        Args:
            stock: 待评分的新股

        Returns:
            定价得分（0-100）
        """
        # 计算隐含市值和市盈率
        mid_price = (stock.price_low + stock.price_high) / 2.0

        if stock.net_profit_ttm is not None and stock.net_profit_ttm > 0:
            # 有正利润：可以计算 P/E
            # 假设发行后总股本 ≈ 入场费 / (每手股数 × 中间价) × 某个倍数
            # 简化处理：直接用市值/利润的比例来评分
            # 使用收入和利润的关系来推算合理性
            implied_pe = (stock.revenue_ttm or 1.0) / stock.net_profit_ttm * 15.0

            if 10 <= implied_pe <= 25:
                return 90.0  # 理想 P/E 区间
            elif 5 <= implied_pe < 10 or 25 < implied_pe <= 40:
                return 70.0  # 可接受区间
            elif implied_pe > 40:
                return 40.0  # 偏高
            else:
                return 50.0  # P/E 过低可能有陷阱
        elif stock.net_profit_ttm is not None and stock.net_profit_ttm <= 0:
            # 亏损企业：根据毛利率和赛道综合评分
            gm = stock.gross_margin or 0.0
            if gm >= 50:
                # 高毛利亏损企业（可能是研发阶段的创新药/科技股）
                return 55.0
            elif gm >= 20:
                return 40.0
            else:
                # 低毛利还亏损，定价风险较大
                return 25.0
        else:
            # 无利润数据
            return 50.0

    # ================================================================
    # ROI 预测
    # ================================================================

    def _calc_roi(
        self,
        score_fundamental: float,
        score_cornerstone: float,
        score_sponsor: float,
        score_sentiment: float,
        score_pricing: float,
        market_beta: float,
    ) -> tuple[float, float, float]:
        """
        计算 ROI 预测区间（乐观 / 中性 / 悲观）。

        核心公式：
            ROI_neutral = α·CornerScore + β·SponsorScore + γ·SentimentScore
                         + δ·FundamentalScore - PricingPenalty

        其中各系数将分项得分（0-100）映射到合理的 ROI 贡献范围。
        最终结果乘以 MarketBeta 大盘调节系数。

        Args:
            score_fundamental: 基本面得分
            score_cornerstone: 基石得分
            score_sponsor: 保荐人得分
            score_sentiment: 市场情绪得分
            score_pricing: 定价得分
            market_beta: 大盘调节系数

        Returns:
            (roi_neutral, roi_optimistic, roi_pessimistic) 三元组，单位 %
        """
        # 各因子的 ROI 贡献系数（将 0-100 分映射到百分比收益贡献）
        # α: 基石得分贡献，基石占比高 → 上市后抛压小 → ROI 正贡献
        alpha = 0.12  # 基石满分贡献 +12%
        # β: 保荐人得分贡献，优质保荐人 → 定价合理 → ROI 正贡献
        beta = 0.10   # 保荐人满分贡献 +10%
        # γ: 情绪得分贡献，高热度 → 首日需求旺盛 → ROI 正贡献
        gamma = 0.15  # 情绪满分贡献 +15%
        # δ: 基本面得分贡献，基本面好 → 长期支撑 → ROI 正贡献
        delta = 0.08  # 基本面满分贡献 +8%

        # 定价惩罚：定价越不合理，惩罚越大
        # 满分时无惩罚，0分时惩罚 -15%
        pricing_penalty = (1.0 - score_pricing / 100.0) * 15.0

        # 中性 ROI（基础值）
        roi_base = (
            alpha * score_cornerstone
            + beta * score_sponsor
            + gamma * score_sentiment
            + delta * score_fundamental
            - pricing_penalty
        )

        # 减去基准偏移：当所有分项为 50（中间值）时，ROI 应接近 0
        # 中间值时的原始 ROI = 0.12*50 + 0.10*50 + 0.15*50 + 0.08*50 - 7.5
        #                     = 6 + 5 + 7.5 + 4 - 7.5 = 15.0
        # 我们需要让中间值 → ~0%，所以减去这个偏移量
        baseline_offset = 15.0
        roi_neutral = roi_base - baseline_offset

        # 应用 MarketBeta 大盘调节系数
        roi_neutral *= market_beta

        # 情景分析
        roi_optimistic = roi_neutral * ScoreWeights.ROI_OPTIMISTIC_MULT
        roi_pessimistic = (
            roi_neutral * ScoreWeights.ROI_PESSIMISTIC_MULT
            + ScoreWeights.ROI_PESSIMISTIC_OFFSET
        )

        return roi_neutral, roi_optimistic, roi_pessimistic

    # ================================================================
    # 破发概率
    # ================================================================

    def _calc_break_probability(self, ai_score: float) -> float:
        """
        计算首日破发概率。

        修正公式：
            break_prob = 1 - (ai_score / 100) ^ 0.7

        使用 0.7 次方进行修正，使得：
        - 高分（80+）时破发概率较低但不会趋近于 0
        - 中分（50）时破发概率约 38%
        - 低分（30）时破发概率约 58%

        Args:
            ai_score: AI 综合评分（0-100）

        Returns:
            破发概率（0-1）
        """
        normalized = max(0.0, min(ai_score / 100.0, 1.0))
        # 使用幂次修正，避免极端值
        break_prob = 1.0 - (normalized ** 0.7)
        return max(0.0, min(break_prob, 1.0))

    # ================================================================
    # 行动建议映射
    # ================================================================

    def _map_recommendation(
        self, ai_score: float, break_probability: float
    ) -> RecommendAction:
        """
        根据 AI 评分和破发概率映射行动建议。

        映射规则：
        - ≥75 分且破发概率 <25% → 全力申购
        - 50-74 分（或破发概率在 25%-50%）→ 现金一手摸
        - <50 分 → 放弃

        使用 config.RecommendationLevel 的配置进行映射。

        Args:
            ai_score: AI 综合评分
            break_probability: 破发概率

        Returns:
            行动建议枚举值
        """
        level = RecommendationLevel.get_level(ai_score, break_probability)
        label = level["label"]

        # 将 label 映射回 RecommendAction 枚举
        label_to_action = {
            "全力申购": RecommendAction.FULL_BUY,
            "现金一手摸": RecommendAction.ONE_LOT,
            "放弃": RecommendAction.SKIP,
        }
        return label_to_action.get(label, RecommendAction.SKIP)

    # ================================================================
    # 文本生成
    # ================================================================

    def _generate_recommendation_text(
        self,
        stock: IPOStock,
        ai_score: float,
        break_probability: float,
        recommendation: RecommendAction,
    ) -> str:
        """
        生成通俗易懂的行动建议文字说明。

        Args:
            stock: 新股数据
            ai_score: AI 综合评分
            break_probability: 破发概率
            recommendation: 行动建议

        Returns:
            建议文字说明
        """
        # 基石描述
        corner_names = [inv.name for inv in stock.cornerstone_investors]
        corner_pct = stock.cornerstone_total_pct
        if corner_names:
            corner_desc = (
                f"基石投资者（{'、'.join(corner_names[:3])}）"
                f"合计认购 {corner_pct:.0f}%"
            )
        else:
            corner_desc = "无基石投资者"

        # 保荐人描述
        sponsor_names = [sp.name for sp in stock.sponsors]
        if sponsor_names:
            best_br = min(sp.break_rate_2yr for sp in stock.sponsors)
            sponsor_desc = (
                f"保荐人{'、'.join(sponsor_names)}"
                f"近两年最佳破发率 {best_br:.0%}"
            )
        else:
            sponsor_desc = "保荐人信息未知"

        # 孖展描述
        margin = stock.sentiment.margin_subscription_multiple
        if margin is not None:
            margin_desc = f"孖展 {margin:.0f} 倍"
        else:
            margin_desc = "孖展数据暂无"

        # 组合建议
        if recommendation == RecommendAction.FULL_BUY:
            action = "建议全力申购"
        elif recommendation == RecommendAction.ONE_LOT:
            action = "建议仅用现金申购一手试水"
        else:
            action = "建议放弃本轮申购"

        return (
            f"{corner_desc}，{sponsor_desc}，{margin_desc}。"
            f"破发概率 {break_probability:.0%}，{action}。"
        )

    def _generate_analysis_summary(
        self,
        stock: IPOStock,
        ai_score: float,
        score_fundamental: float,
        score_cornerstone: float,
        score_sponsor: float,
        score_sentiment: float,
        score_pricing: float,
        roi_neutral: float,
        break_probability: float,
    ) -> str:
        """
        生成 AI 分析总结（2-3 句话）。

        Args:
            stock: 新股数据
            ai_score: AI 综合评分
            其余参数: 各维度得分和预测值

        Returns:
            分析总结文字
        """
        # 找出最强和最弱的维度
        dimensions = {
            "基本面": score_fundamental,
            "基石投资者": score_cornerstone,
            "保荐人": score_sponsor,
            "市场情绪": score_sentiment,
            "定价合理性": score_pricing,
        }
        strongest = max(dimensions, key=dimensions.get)  # type: ignore
        weakest = min(dimensions, key=dimensions.get)    # type: ignore

        strength_desc = f"最强维度为{strongest}（{dimensions[strongest]:.0f}分）"
        weakness_desc = f"最弱维度为{weakest}（{dimensions[weakest]:.0f}分）"

        return (
            f"综合评分 {ai_score:.1f} 分。{strength_desc}，{weakness_desc}。"
            f"中性 ROI 预测 {roi_neutral:+.1f}%，"
            f"破发概率 {break_probability:.0%}。"
        )
