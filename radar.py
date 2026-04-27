import streamlit as st
import pandas as pd
import requests
from datetime import datetime

st.set_page_config(page_title="🚀 妖幣起飛雷達 v2.0", layout="wide", page_icon="🚀")

st.title("🚀 妖幣起飛雷達 v2.0")
st.markdown("**Gate.io Stable Data** | 避開頻率限制，穩定獲取行情")

# ====================== 穩定數據獲取函數 ======================
@st.cache_data(ttl=30)
def get_stable_data():
    # Gate.io 的 API 對雲端伺服器非常寬鬆，幾乎不擋 IP
    url = "https://gateio.ws"
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code != 200:
            st.warning("數據源稍快，請按按鈕重新刷一次。")
            return pd.DataFrame()
            
        data = resp.json()
        df = pd.DataFrame(data)
        
        # 過濾 USDT 交易對
        df = df[df['currency_pair'].str.endswith('_USDT')]
        
        # 轉換數值並重命名
        df['last'] = pd.to_numeric(df['last'])
        df['change'] = pd.to_numeric(df['change_percentage'])
        df['volume'] = pd.to_numeric(df['base_volume'])
        
        # 簡易評分與訊號
        df['score'] = (df['change'] * 2 + (df['volume'] > 10000) * 10).round(1)
        df['signal'] = df['score'].apply(lambda x: "🚀 強買入" if x > 30 else "📈 吸籌中" if x > 10 else "🔍 觀察")
        
        return df.sort_values('score', ascending=False).reset_index(drop=True)

    except:
        return pd.DataFrame()

# ====================== UI 顯示 ======================
if st.button("🔄 立即刷新行情數據"):
    st.cache_data.clear()
    st.rerun()

df = get_stable_data()

if not df.empty:
    top = df.iloc[0]
    st.success(f"🔥 全網最強勢標的：{top['currency_pair']} (漲幅: {top['change']}%)")
    
    # 格式化表格
    display = df[['currency_pair', 'last', 'change', 'volume', 'signal', 'score']]
    display.columns = ['交易對', '最新價', '24h漲跌%', '24h成交量', '訊號', '綜合評分']
    
    st.dataframe(display.head(50), use_container_width=True, hide_index=True)
else:
    st.info("💡 正在從 Gate.io 獲取穩定數據流... 請稍候。")

st.caption(f"數據來源: Gate.io API | 最後更新: {datetime.now().strftime('%H:%M:%S')}")
