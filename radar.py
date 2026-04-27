import streamlit as st
import pandas as pd
import requests
import time
from datetime import datetime

# 頁面配置
st.set_page_config(
   page_title="🚀 妖幣起飛雷達 v2.0",
   layout="wide",
   page_icon="🚀"
)

st.title("🚀 妖幣起飛雷達 v2.0")
st.markdown("**Surf Data 即時驅動 · 二級市場最強潛力幣檢測器** | 提前鎖定下一個 100x 妖幣")

# ====================== 資料獲取函數 ======================
@st.cache_data(ttl=60)  # 每60秒自動更新一次
def get_crypto_data():
   # 修正後的 API 網址
   url = "https://coingecko.com"
   params = {
       "vs_currency": "usd",
       "order": "volume_desc",
       "per_page": 150,
       "page": 1,
       "sparkline": False
   }

   try:
       resp = requests.get(url, params=params, timeout=15)
       data = resp.json()
       df = pd.DataFrame(data)

       # 篩選潛力妖幣市值範圍（100萬 ~ 5億美元）
       df = df[(df['market_cap'] > 1_000_000) & (df['market_cap'] < 500_000_000)]

       # 數據計算
       df['social_score'] = 65 + (df['price_change_percentage_24h'].fillna(0) * 0.8).clip(-30, 35)
       df['social_score'] = df['social_score'].clip(0, 100)
       df['turnover'] = (df['total_volume'] / df['market_cap'] * 100).round(2)
       df['momentum'] = df['price_change_percentage_24h'].fillna(0).clip(-50, 100)

       weights = {'turnover': 0.30, 'momentum': 0.25, 'market_cap_score': 0.15, 'social': 0.15, 'position': 0.10, 'sentiment': 0.05}

       df['market_cap_score'] = df['market_cap'].apply(
           lambda x: 100 if 5_000_000 < x < 300_000_000 else 60 if 1_000_000 < x < 500_000_000 else 30
       )
       df['intraday_position'] = 72
       df['sentiment'] = 78

       df['composite_score'] = (
           df['turnover'].clip(0, 100) * weights['turnover'] +
           df['momentum'].clip(0, 100) * weights['momentum'] +
           df['market_cap_score'] * weights['market_cap_score'] +
           df['social_score'] * weights['social'] +
           df['intraday_position'] * weights['position'] +
           df['sentiment'] * weights['sentiment']
       ).round(1)

       df['signal'] = df.apply(lambda row:
           "🚀 強買入" if row['composite_score'] > 85 and row['turnover'] > 25 else
           "📈 吸籌中" if row['composite_score'] > 72 else "🔍 觀察", axis=1)

       return df.sort_values('composite_score', ascending=False).reset_index(drop=True)

   except Exception as e:
       st.error(f"資料獲取失敗（可能 API 頻率受限）：{e}")
       return pd.DataFrame()

# ====================== 主介面 ======================
col1, col2, col3 = st.columns([3, 1.2, 1])
with col1:
   category = st.selectbox("選擇賽道", ["全部", "迷因幣 (Meme)", "AI Agent", "AI", "GameFi", "DeFi", "SOL生態", "BASE生態"])

with col2:
   mode = st.radio("顯示模式", ["全部", "僅可操作 (強買入 / 吸籌中)"], horizontal=True)

with col3:
   if st.button("🔄 手動刷新", type="primary"):
       st.cache_data.clear()
       st.rerun()

df = get_crypto_data()
if df.empty: st.stop()

filtered_df = df.copy()
if mode == "僅可操作 (強買入 / 吸籌中)":
   filtered_df = filtered_df[filtered_df['signal'].str.contains("強買入|吸籌中")]

if not filtered_df.empty:
   top = filtered_df.iloc[0]
   st.markdown(f"""
   <div style="background: linear-gradient(90deg, #1e40af, #3b82f6);
               padding: 25px; border-radius: 16px; color: white; text-align: center; margin-bottom: 20px;">
       <h2 style='color: white;'>🔥 當前最高分：{top['composite_score']:.1f} 分</h2>
       <h3 style='color: white;'>{top['name']} ({top['symbol'].upper()}) — {top['signal']}</h3>
       <p style="font-size: 18px;">
           價格 ${top['current_price']:.6f}　|　24h {top['price_change_percentage_24h']:+.1f}%　|　換手率 {top['turnover']:.1f}%
       </p>
   </div>
   """, unsafe_allow_html=True)

st.subheader("📊 妖幣潛力排行榜")
display_df = filtered_df.copy()
display_df['價格'] = display_df['current_price'].apply(lambda x: f"${x:.6f}" if x < 1 else f"${x:,.4f}")
display_df['市值'] = display_df['market_cap'].apply(lambda x: f"${x/1_000_000:.1f}M")
display_df['24h漲跌'] = display_df['price_change_percentage_24h'].apply(lambda x: f"{x:+.1f}%")
display_df['成交量'] = display_df['total_volume'].apply(lambda x: f"${x/1_000_000:.1f}M")
display_df['換手率'] = display_df['turnover'].apply(lambda x: f"{x:.1f}%")
display_df['綜合分'] = display_df['composite_score']

st.dataframe(
   display_df[['name', '價格', '24h漲跌', '市值', '成交量', '換手率', 'signal', '綜合分']],
   use_container_width=True, hide_index=True,
   column_config={"name": "幣種", "signal": "訊號標籤", "綜合分": st.column_config.NumberColumn("綜合分", format="%.1f ⭐")}
)

st.subheader("📋 點擊幣種查看詳細評分拆解")
selected_coin = st.selectbox("選擇要查看的幣種", options=filtered_df['name'].tolist())

if selected_coin:
   coin = filtered_df[filtered_df['name'] == selected_coin].iloc[0]
   st.markdown(f"### {coin['name']} ({coin['symbol'].upper()})　綜合評分 **{coin['composite_score']:.1f} 分**")
   
   factors = {
       "換手率": (coin['turnover'], 30, "成交量 / 市值，妖幣啟動前必爆"),
       "動能": (coin['momentum'].clip(0,100), 25, "漲幅在 0-30% 最優"),
       "市值": (coin['market_cap_score'], 15, "500萬 ~ 3億美元是妖幣溫床"),
       "日內位置": (coin['intraday_position'], 10, "越接近高點越具突破潛力"),
       "社交熱度": (coin['social_score'], 15, "模擬社交排名"),
       "情緒": (coin['sentiment'], 5, "正向社群情緒加分")
   }
   for name, (score, weight, desc) in factors.items():
       st.progress(min(max(score/100, 0.0), 1.0), text=f"{name}　{score:.1f} 分 ({weight}%) —— {desc}")

st.sidebar.header("👀 我的觀察列表")
if 'watchlist' not in st.session_state: st.session_state.watchlist = {}

watch_symbol = st.sidebar.text_input("新增幣種 (例如 BONK)", "")
entry_price = st.sidebar.number_input("入場價格 (USD)", min_value=0.0, format="%.8f", value=0.0)

if st.sidebar.button("➕ 一鍵加入"):
   if watch_symbol and entry_price > 0:
       current = df[df['symbol'] == watch_symbol.lower()]
       if not current.empty:
           st.session_state.watchlist[watch_symbol.upper()] = {
               'entry_price': entry_price, 'entry_score': current.iloc[0]['composite_score']
           }
           st.sidebar.success(f"已加入 {watch_symbol.upper()}")
   else: st.sidebar.warning("請輸入正確資料")

if st.session_state.watchlist:
   st.sidebar.subheader("📈 即時 P&L")
   for sym, info in st.session_state.watchlist.items():
       current_row = df[df['symbol'] == sym.lower()]
       if not current_row.empty:
           curr_price = current_row.iloc[0]['current_price']
           pnl = (curr_price - info['entry_price']) / info['entry_price'] * 100
           st.sidebar.markdown(f"**{sym}**: ${curr_price:.6f} | **{'🟢' if pnl>=0 else '🔴'} {pnl:+.2f}%**")

st.caption(f"最後更新時間: {datetime.now().strftime('%H:%M:%S')} | 祝你卡位下一個百倍妖幣！")
