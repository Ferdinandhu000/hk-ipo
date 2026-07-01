# -*- coding: utf-8 -*-
"""
新股雷达 Agent（IPO Scanner）

职责：
    持续追踪港交所最新的 IPO 招股动态，包括：
    - 即将招股、正在招股、等待上市的新股列表
    - 基础信息采集（公司名称、股票代码、行业赛道、招股日期、发行价区间等）

工作模式：
    - Demo 模式：直接返回 sample_data 中预设的模拟新股基础信息
    - Live 模式：预留 web search 接口，后续接入实时数据源（当前为 stub）
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from data.models import DataMode, IPOStock

if TYPE_CHECKING:
    pass


class IPOScannerAgent:
    """
    新股雷达 Agent

    负责扫描港交所最新的 IPO 招股信息，输出新股列表。
    是整个 Agent 管线的第一环，为后续分析 Agent 提供原始数据。

    Attributes:
        mode: 数据获取模式（demo / live）
    """

    def __init__(self, mode: DataMode = DataMode.DEMO):
        """
        初始化新股雷达 Agent。

        Args:
            mode: 数据模式，默认 Demo
        """
        self.mode = mode

    def run(self) -> list[IPOStock]:
        """
        执行新股扫描任务。

        Returns:
            新股列表（IPOStock 实例，仅包含基础信息，AI 分析字段为默认值）

        Raises:
            NotImplementedError: Live 模式下的 web search 尚未实现
        """
        if self.mode == DataMode.DEMO:
            return self._run_demo()
        else:
            return self._run_live()

    def _run_demo(self) -> list[IPOStock]:
        """
        Demo 模式：从 sample_data 加载模拟新股数据。

        Returns:
            4 只模拟新股的列表
        """
        from data.sample_data import generate_sample_stocks

        stocks = generate_sample_stocks()
        print(f"[IPOScanner] Demo 模式：已加载 {len(stocks)} 只模拟新股")
        return stocks

    def _run_live(self) -> list[IPOStock]:
        """
        Live 模式：通过爬取 AAStocks 实时招股信息。

        Returns:
            新股列表（IPOStock 实例，包含基础信息，AI 分析及其他深度维度待后续 Agent 补充）
        """
        import requests
        from bs4 import BeautifulSoup
        import re
        from datetime import datetime, date, timedelta
        from data.models import MarketSentiment, HeatLevel

        print("[IPOScanner] Live 模式：开始从 AAStocks 抓取新股数据...")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        
        try:
            r = requests.get('https://www.aastocks.com/tc/stocks/market/ipo/upcomingipo.aspx', headers=headers, timeout=15)
            if r.status_code != 200:
                print(f"[IPOScanner] 错误：请求 AAStocks 失败，状态码 {r.status_code}")
                return []
            
            # 使用 apparent_encoding 避免乱码（AAStocks 默认为 Big5）
            soup = BeautifulSoup(r.content, 'html.parser', from_encoding=r.apparent_encoding)
            tbl = soup.find('table', class_='dataTable')
            if not tbl:
                print("[IPOScanner] 错误：未在页面上找到数据表格")
                return []

            stocks = []
            rows = tbl.find_all('tr')[1:]  # 跳过表头
            
            for tr in rows:
                cells = [td.get_text(strip=True) for td in tr.find_all('td')]
                if len(cells) < 9:
                    continue
                
                name_code = cells[1]
                # 正则匹配形如 "安克創新00668.HK"
                m = re.match(r'^(.*?)(0\d{4})\.HK$', name_code)
                if not m:
                    continue
                
                name, code_num = m.groups()
                code = f"{code_num}.HK"
                sector = cells[2]
                price_str = cells[3]
                lot_size_str = cells[4].replace(',', '')
                entry_fee_str = cells[5].replace(',', '')
                sub_end_str = cells[6]
                listing_str = cells[8]
                
                # ---- 解析价格区间 ----
                price_low = 0.0
                price_high = 0.0
                if '-' in price_str:
                    parts = price_str.split('-')
                    try:
                        price_low = float(parts[0])
                        price_high = float(parts[1])
                    except ValueError:
                        pass
                else:
                    try:
                        price_low = price_high = float(price_str)
                    except ValueError:
                        # N/A 时的估算
                        pass

                # ---- 解析每手股数与入场费 ----
                try:
                    lot_size = int(lot_size_str)
                except ValueError:
                    lot_size = 1000  # 默认值
                
                try:
                    entry_fee = float(entry_fee_str)
                except ValueError:
                    entry_fee = price_high * lot_size * 1.010077  # 估算入场费（含手续费）
                
                if price_low == 0.0 or price_high == 0.0:
                    price_high = price_low = entry_fee / lot_size / 1.010077

                # ---- 解析日期 ----
                today_dt = date.today()
                try:
                    subscription_end = datetime.strptime(sub_end_str, "%Y/%m/%d").date()
                except ValueError:
                    subscription_end = today_dt + timedelta(days=2)
                
                try:
                    listing_date = datetime.strptime(listing_str, "%Y/%m/%d").date()
                except ValueError:
                    listing_date = subscription_end + timedelta(days=5)

                subscription_start = subscription_end - timedelta(days=4)

                # ---- 过滤过旧的或者已上市很久的数据，只看正在招股或近期新股 ----
                # 倒计时在 [-7, 60] 天内的新股
                days_to_close = (subscription_end - today_dt).days
                if days_to_close < -7 or days_to_close > 60:
                    continue

                # ---- 匹配行业 Tag 及 Emoji ----
                sector_tag = f"📊 {sector}"
                for key, tag in [
                    ("AI", "🤖 AI / 人工智能"), ("智能", "🤖 AI / 人工智能"), ("芯片", "🔬 半导体"), 
                    ("半導體", "🔬 半导体"), ("生物", "💊 生物医药"), ("醫", "💊 生物医药"),
                    ("藥", "💊 生物医药"), ("新能", "🔋 新能源"), ("汽車", "🚗 智能汽车"),
                    ("零售", "🛒 消费零售"), ("消費", "🛒 消费零售"), ("食品", "🛒 消费零售"),
                    ("地產", "🏗️ 地产建筑"), ("建築", "🏗️ 地产建筑"), ("金融", "🏦 金融服务"),
                    ("銀行", "🏦 金融服务"), ("保險", "🏦 金融服务"), ("軟件", "💻 软件科技"),
                    ("科技", "💻 软件科技"), ("遊戲", "🎮 游戏娱乐"), ("物流", "📦 物流供应链")
                ]:
                    if key in sector or key in name:
                        sector_tag = tag
                        break

                # ---- 大白话业务描述兜底生成 ----
                business_summary = f"{name}是一家深耕于{sector}赛道的企业。公司致力于提供优质的相关业务服务与产品。目前正处于港股IPO上市阶段，计划募集资金用于扩大业务、提升技术创新以及一般日常营运资金。"

                stock = IPOStock(
                    name=name,
                    code=code,
                    sector=sector,
                    sector_tag=sector_tag,
                    subscription_start=subscription_start,
                    subscription_end=subscription_end,
                    listing_date=listing_date,
                    price_low=round(price_low, 2),
                    price_high=round(price_high, 2),
                    lot_size=lot_size,
                    entry_fee=round(entry_fee, 2),
                    business_summary=business_summary,
                    revenue_ttm=None,
                    net_profit_ttm=None,
                    gross_margin=None,
                    cornerstone_investors=[],
                    cornerstone_lock_up_months=6,
                    sponsors=[],
                    sentiment=MarketSentiment(
                        margin_subscription_multiple=None,
                        retail_heat=HeatLevel.MEDIUM,
                        sentiment_summary="正在进行招股，市场逐步加温中",
                        data_source="AAStocks 实时抓取",
                    ),
                    data_fetched_at=datetime.now(),
                )
                stocks.append(stock)
                
            print(f"[IPOScanner] Live 模式：成功抓取并解析 {len(stocks)} 只真实新股")
            return stocks
            
        except Exception as e:
            print(f"[IPOScanner] 异常：抓取实时新股数据失败。原因：{e}")
            return []
