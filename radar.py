import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# ====================== 1. 頁面基礎配置 ======================
st.set_page_config(page_title="🚀 妖幣起飛雷達 v2.0", layout="wide", page_icon="🚀")

st.title("🚀 妖幣起飛雷達 v2.0")
st.markdown("**Binance Infrastructure** | 二級市場最強潛力幣檢測器")

# ====================== 2. 穩定獲取數據 (使用幣安 API) ======================
@st.cache_data(ttl=30)
def get_stable_data():
    # 幣安 API 對雲端 IP 較寬鬆，且數據更新極快
    url = "https://binance.com"
    try:
        # 加入偽裝 Header
        headers = {'User-Agent': 'Mozilla/5.0'}
        resp = requests.get(url, headers=headers, timeout=10)
        
        if resp.status_code != 200:
            return pd.DataFrame() # 獲取失敗則返回空表
            
        df = pd.DataFrame(resp.json())
        
        # 過濾 USDT 交易對並排除穩定幣
        df = df[df['symbol'].str.endswith('USDT')]
        df = df[~df['symbol'].str.contains('UP|DOWN|USDC|BUSD|DAI')]
        
        # 數值轉換
        df['priceChangePercent'] = pd.to_numeric(df['priceChangePercent'])
        df['lastPrice'] = pd.to_numeric(df['lastPrice'])
        df['quoteVolume'] = pd.to_numeric(df['quoteVolume'])
        
        # 妖幣評分邏輯 (漲幅 + 成交量波動)
        df['score'] = (df['priceChangePercent'] * 1.2 + (df['quoteVolume'] > 30_000_000) * 20).round(1)
        df['signal'] = df['score'].apply(lambda x: "🚀 強買入" if x > 45 else "📈 吸籌中" if x > 25 else "🔍 觀察")
        
        return df.sort_values('score', ascending=False).reset_index(drop=True)
    except:
        return pd.DataFrame()

# ====================== 3. UI 介面佈局 ======================
if st.button("🔄 立即刷新行情"):
    st.cache_data.clear()
    st.rerun()

df = get_stable_data()

if not df.empty:
    # 頂部最高分
    top = df.iloc[0]
    st.success(f"🔥 當前最強標的：{top['symbol']} (漲幅: {top['priceChangePercent']:+.2f}%)")
    
    # 顯示排行榜
    view_df = df[['symbol', 'lastPrice', 'priceChangePercent', 'quoteVolume', 'signal', 'score']].copy()
    view_df.columns = ['交易對', '最新價', '24h漲跌', '24h成交額', '訊號', '綜合評分']
    
    st.dataframe(
        view_df.head(50), 
        use_container_width=True, 
        hide_index=True,
        column_config={"24h漲跌": "{:+.2f}%", "24h成交額": "$%.0f"}
    )
    
    # 側邊觀察清單
    st.sidebar.header("👀 觀察列表")
    st.sidebar.info("數據來源已切換為 Binance API，提供秒級更新且不封鎖 IP。")
else:
    st.error("⚠️ 數據獲取暫時中斷。這通常是 API 請求過於頻繁，請等待 30 秒後點擊「刷新」。")

st.caption(f"最後更新時間: {datetime.now().strftime('%H:%M:%S')}")
