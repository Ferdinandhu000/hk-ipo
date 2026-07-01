# -*- coding: utf-8 -*-
"""
全局配置模块

定义颜色主题、常量、Session State 键名等全局配置。
采用暗色主题 + Glassmorphism 风格。
"""

# ============================================================
# 🎨 颜色主题（暗色 + 渐变玻璃态）
# ============================================================

class Colors:
    """看板配色方案"""

    # ---- 背景 ----
    BG_PRIMARY = "#0E1117"        # 主背景（深空黑）
    BG_SECONDARY = "#1A1D29"      # 二级背景（卡片底色）
    BG_CARD = "rgba(30, 34, 50, 0.7)"  # 玻璃态卡片背景

    # ---- 主色调 ----
    ACCENT_PURPLE = "#6C5CE7"     # 渐变紫（品牌主色）
    ACCENT_BLUE = "#00B4D8"       # 科技蓝
    ACCENT_CYAN = "#00E5FF"       # 高亮青
    ACCENT_PINK = "#FF6B9D"       # 点缀粉

    # ---- 语义色 ----
    GREEN = "#00E676"             # 推荐 / 看涨
    YELLOW = "#FFD600"            # 中性 / 谨慎
    RED = "#FF5252"               # 警告 / 破发
    ORANGE = "#FF9100"            # 注意

    # ---- 文字 ----
    TEXT_PRIMARY = "#EAEAEA"      # 主文字（亮灰）
    TEXT_SECONDARY = "#8B95A5"    # 辅助文字（暗灰）
    TEXT_MUTED = "#4A5568"        # 弱文字

    # ---- 边框与分割线 ----
    BORDER = "rgba(108, 92, 231, 0.3)"   # 半透明紫色边框
    DIVIDER = "rgba(255, 255, 255, 0.08)" # 分割线

    # ---- 渐变 ----
    GRADIENT_PRIMARY = "linear-gradient(135deg, #6C5CE7 0%, #00B4D8 100%)"
    GRADIENT_CARD = "linear-gradient(135deg, rgba(108,92,231,0.15) 0%, rgba(0,180,216,0.08) 100%)"
    GRADIENT_SCORE_HIGH = "linear-gradient(135deg, #00E676 0%, #00B4D8 100%)"
    GRADIENT_SCORE_MID = "linear-gradient(135deg, #FFD600 0%, #FF9100 100%)"
    GRADIENT_SCORE_LOW = "linear-gradient(135deg, #FF5252 0%, #FF6B9D 100%)"


# ============================================================
# 📐 布局常量
# ============================================================

class Layout:
    """布局相关常量"""
    PAGE_TITLE = "🎯 港股打新雷达 · AI 智能推荐看板"
    PAGE_ICON = "🎯"
    SIDEBAR_WIDTH = 300  # 侧边栏宽度（px）


# ============================================================
# 🔑 Session State 键名
# ============================================================

class SessionKeys:
    """
    统一管理 st.session_state 中的键名。
    所有组件必须通过这些键名存取数据，禁止硬编码字符串。
    """
    # 核心数据（Orchestrator 写入，组件只读）
    IPO_DATA = "ipo_data"                      # List[IPOStock] 完整新股数据列表
    LAST_REFRESH = "last_refresh"              # datetime 上次刷新时间
    DATA_LOADED = "data_loaded"                # bool 数据是否已加载
    MARKET_BETA = "market_beta"                # float 大盘调节系数

    # UI 状态（组件读写）
    SELECTED_STOCK = "selected_stock"          # Optional[str] 当前选中的股票代码
    VIEW_MODE = "view_mode"                    # "radar" | "detail" 当前视图
    DATA_MODE = "data_mode"                    # "demo" | "live" 数据模式
    SHOW_DETAIL = "show_detail"                # bool 是否展示详情面板


# ============================================================
# 📊 评分模型参数
# ============================================================

class ScoreWeights:
    """
    Quant Agent 评分模型的权重配置。
    总权重 = 1.0
    """
    FUNDAMENTAL = 0.25    # 基本面质量
    CORNERSTONE = 0.20    # 基石投资者占比
    SPONSOR = 0.20        # 保荐人历史胜率
    SENTIMENT = 0.20      # 市场热度
    PRICING = 0.15        # 发行定价合理性

    # ROI 预测的情景乘数
    ROI_OPTIMISTIC_MULT = 1.8     # 乐观情景 = 中性 × 1.8
    ROI_PESSIMISTIC_MULT = 0.3    # 悲观情景 = 中性 × 0.3 - 5%
    ROI_PESSIMISTIC_OFFSET = -5.0 # 悲观情景偏移量（%）

    # 大盘调节系数范围
    MARKET_BETA_MIN = 0.5         # 极度熊市最低调节系数
    MARKET_BETA_MAX = 1.2         # 牛市最高调节系数
    MARKET_BETA_DEFAULT = 1.0     # 默认（中性市场）


# ============================================================
# 🏷️ 建议等级映射
# ============================================================

class RecommendationLevel:
    """行动建议等级定义"""

    # (最低分, 最高分, 最高破发概率, 标签, 颜色, emoji)
    LEVELS = [
        {
            "min_score": 75,
            "max_break_prob": 0.25,
            "label": "全力申购",
            "color": Colors.GREEN,
            "emoji": "🟢",
            "description": "各项指标优秀，建议积极参与"
        },
        {
            "min_score": 50,
            "max_break_prob": 0.50,
            "label": "现金一手摸",
            "color": Colors.YELLOW,
            "emoji": "🟡",
            "description": "指标尚可，建议仅用现金申购一手试水"
        },
        {
            "min_score": 0,
            "max_break_prob": 1.0,
            "label": "放弃",
            "color": Colors.RED,
            "emoji": "🔴",
            "description": "风险较高，建议本轮不参与"
        },
    ]

    @classmethod
    def get_level(cls, score: float, break_prob: float) -> dict:
        """根据 AI 分数和破发概率返回对应的建议等级"""
        for level in cls.LEVELS:
            if score >= level["min_score"] and break_prob <= level["max_break_prob"]:
                return level
        # 兜底：返回最保守建议
        return cls.LEVELS[-1]


# ============================================================
# 🏷️ 赛道标签
# ============================================================

SECTOR_TAGS = [
    "🤖 AI / 人工智能",
    "💊 生物医药",
    "🔋 新能源",
    "🛒 消费零售",
    "🏗️ 地产建筑",
    "💻 软件科技",
    "🏦 金融服务",
    "🏭 先进制造",
    "🎮 游戏娱乐",
    "📦 物流供应链",
    "🔬 半导体",
    "🚗 智能汽车",
]


# ============================================================
# ⏱️ 缓存配置
# ============================================================

class CacheConfig:
    """缓存相关配置"""
    CACHE_DIR = "data/cache"
    CACHE_TTL_HOURS = 4           # 缓存有效期（小时）
    SEARCH_TIME_FILTER_DAYS = 60  # Web Search 时间过滤（最近 N 天）
