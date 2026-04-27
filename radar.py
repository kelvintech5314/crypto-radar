import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# ====================== 1. 頁面配置 ======================
st.set_page_config(
   page_title="🚀 幣安妖幣雷達 v2.0",
   layout="wide",
   page_icon="🚀"
)

st.title("🚀 幣安妖幣起飛雷達 v2.0")
st.markdown("**Binance Real-time Data** | 幣安二級市場最強潛力幣檢測器")

# ====================== 2. 幣安資料獲取函數 ======================
@st.cache_data(ttl=30)  # 每 30 秒自動更新一次
def get_binance_data():
   try:
       # 獲取幣安所有交易對的 24h 價格動態
       url = "https://binance.com"
       resp = requests.get(url, timeout=10)
       data = resp.json()
       
       df = pd.DataFrame(data)
       
       # 篩選: 只看 USDT 交易對，且排除槓桿代幣 (UP/DOWN) 與穩定幣
       df = df[df['symbol'].str.endswith('USDT')]
       df = df[~df['symbol'].str.contains('UP|DOWN|USDC|BUSD|DAI|EUR|GBP')]
       
       # 轉換數值類型
       df['lastPrice'] = df['lastPrice'].astype(float)
       df['priceChangePercent'] = df['priceChangePercent'].astype(float)
       df['quoteVolume'] = df['quoteVolume'].astype(float)  # 24小時成交額 (USDT)
       df['count'] = df['count'].astype(int)              # 24小時成交筆數
       
       # ----------------- 妖幣評分邏輯 -----------------
       # 權重：漲幅 (40%) + 成交額活躍度 (40%) + 成交筆數 (20%)
       # 我們尋找「價格有波動」且「資金正瘋狂湧入」的標的
       df['score'] = (
           df['priceChangePercent'].clip(-10, 30) * 2 +          # 漲幅評分
           (df['quoteVolume'] > 50_000_000) * 20 +                # 成交量過 5000 萬加分
           (df['quoteVolume'] > 10_000_000) * 10 +                # 成交量過 1000 萬加分
           (df['count'] / 50000).clip(0, 10)                      # 成交頻率評分
       ).round(1)
       
       # 訊號標籤
       df['signal'] = df.apply(lambda row:
           "🚀 強買入" if row['score'] > 55 and row['priceChangePercent'] > 5 else
           "📈 吸籌中" if row['score'] > 35 else
           "🔍 觀察", axis=1)
       
       # 按照評分排序
       return df.sort_values('score', ascending=False).reset_index(drop=True)

   except Exception as e:
       st.error(f"幣安 API 連線異常：{e}")
       return pd.DataFrame()

# ====================== 3. 主介面顯示 ======================
# 頂部控制列
col1, col2, col3 = st.columns([2, 1.5, 1])
with col3:
   if st.button("🔄 立即刷新行情", type="primary"):
       st.cache_data.clear()
       st.rerun()

df = get_binance_data()

if not df.empty:
   # 1. 頂部最高分看板
   top_coin = df.iloc[0]
   st.markdown(f"""
   <div style="background: linear-gradient(90deg, #f3ba2f, #f0b90b);
               padding: 20px; border-radius: 12px; color: black; text-align: center; margin-bottom: 20px;">
       <h2 style='color: black; margin: 0;'>🔥 幣安強勢標的：{top_coin['symbol']}</h2>
       <h3 style='color: black; margin: 5px;'>當前評分：{top_coin['score']} 分 — {top_coin['signal']}</h3>
       <p style="font-size: 18px; margin: 0;">
           價格 ${top_coin['lastPrice']:.4f}　|　24h 漲跌 {top_coin['priceChangePercent']:+.2f}%　|　成交額 ${top_coin['quoteVolume']/1_000_000:.1f}M
       </p>
   </div>
   """, unsafe_allow_html=True)

   # 2. 排行榜表格
   st.subheader("📊 幣安實時異動排行")
   
   # 整理顯示用 DataFrame
   display_df = df[['symbol', 'lastPrice', 'priceChangePercent', 'quoteVolume', 'signal', 'score']].copy()
   display_df.columns = ['交易對', '最新價', '24h漲跌', '24h成交額', '訊號狀態', '綜合評分']
   
   # 表格美化配置
   st.dataframe(
       display_df,
       use_container_width=True,
       hide_index=True,
       column_config={
           "24h漲跌": st.column_config.NumberColumn("24h漲跌", format="%.2f%%"),
           "24h成交額": st.column_config.NumberColumn("24h成交額 (USDT)", format="$%.0f"),
           "綜合評分": st.column_config.NumberColumn("綜合評分", format="%.1f ⭐")
       }
   )

   # 3. 側邊欄簡易觀察列表
   st.sidebar.header("👀 關注清單")
   if 'my_watch' not in st.session_state: st.session_state.my_watch = []
   
   add_sym = st.sidebar.text_input("新增幣種 (例: BTC)", "").upper()
   if st.sidebar.button("加入清單"):
       if add_sym and not add_sym.endswith("USDT"): add_sym += "USDT"
       if add_sym not in st.session_state.my_watch:
           st.session_state.my_watch.append(add_sym)
           st.rerun()

   for s in st.session_state.my_watch:
       row = df[df['symbol'] == s]
       if not row.empty:
           p = row.iloc[0]['lastPrice']
           c = row.iloc[0]['priceChangePercent']
           st.sidebar.write(f"**{s}**: ${p:.4f} ({'🟢' if c>=0 else '🔴'} {c:+.2f}%)")

else:
   st.warning("⚠️ 數據獲取中，請稍候...")

st.caption(f"數據來源: Binance API (無需 Key) | 最後更新: {datetime.now().strftime('%H:%M:%S')}")
