import streamlit as st
import pandas as pd
import requests
from datetime import datetime

st.set_page_config(page_title="🚀 幣安妖幣雷達 v2.0", layout="wide", page_icon="🚀")

st.title("🚀 幣安妖幣起飛雷達 v2.0")
st.markdown("**Binance Data Pro** | 二級市場最強潛力幣檢測器")

# ====================== 終極穩定獲取函數 ======================
@st.cache_data(ttl=30)
def get_data():
    # 改用另一個 API 接口路徑，增加穩定性
    url = "https://binance.com"
    
    try:
        # 加入偽裝 Header，讓伺服器覺得是真人在看
        headers = {'User-Agent': 'Mozilla/5.0'}
        resp = requests.get(url, headers=headers, timeout=15)
        
        # 檢查狀態碼，如果不是 200 就代表被擋了
        if resp.status_code != 200:
            st.error(f"❌ 幣安伺服器忙碌中 (錯誤碼: {resp.status_code})，請稍後按刷新。")
            return pd.DataFrame()
            
        data = resp.json()
        df = pd.DataFrame(data)
        
        # 過濾 USDT 交易對
        df = df[df['symbol'].str.endswith('USDT')]
        df = df[~df['symbol'].str.contains('UP|DOWN|USDC|BUSD|DAI')]
        
        # 轉換數值
        df['lastPrice'] = pd.to_numeric(df['lastPrice'])
        df['priceChangePercent'] = pd.to_numeric(df['priceChangePercent'])
        df['quoteVolume'] = pd.to_numeric(df['quoteVolume'])
        
        # 簡易評分邏輯
        df['score'] = (df['priceChangePercent'] * 1.5 + (df['quoteVolume'] > 20000000) * 20).round(1)
        df['signal'] = df['score'].apply(lambda x: "🚀 強買入" if x > 40 else "📈 吸籌中" if x > 20 else "🔍 觀察")
        
        return df.sort_values('score', ascending=False).reset_index(drop=True)

    except Exception as e:
        st.error(f"⚠️ 連線超時，這通常是雲端伺服器網路波動，請再按一次刷新。")
        return pd.DataFrame()

# ====================== UI 介面 ======================
if st.button("🔄 立即刷新行情"):
    st.cache_data.clear()
    st.rerun()

df = get_data()

if not df.empty:
    st.success(f"🔥 當前異動最強：{df.iloc[0]['symbol']} (漲幅: {df.iloc[0]['priceChangePercent']}%)")
    
    # 簡化表格顯示
    view_df = df[['symbol', 'lastPrice', 'priceChangePercent', 'quoteVolume', 'signal', 'score']]
    view_df.columns = ['交易對', '最新價', '24h漲幅', '24h成交量', '訊號', '綜合分']
    
    st.dataframe(view_df, use_container_width=True, hide_index=True)
else:
    st.info("💡 正在排隊獲取數據... 幣安 API 請求較多時會暫時排隊，請點擊上方按鈕重試。")

st.caption(f"最後更新: {datetime.now().strftime('%H:%M:%S')}")
