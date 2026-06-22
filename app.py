import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px

st.set_page_config(page_title="投資組合儀表板", layout="wide")

# 1. 載入資料
@st.cache_data
def load_data():
# 使用 Python 原生方式讀取檔案內容，解決編碼與格式問題
    with open("invest_data.csv", "rb") as f:
        content = f.read()
    
    # 自動偵測編碼 (如果 utf-8-sig 不行，我們嘗試用 big5，這是在處理傳統 Excel 匯出最常遇到的情況)
    try:
        decoded_content = content.decode('utf-8-sig')
    except UnicodeDecodeError:
        decoded_content = content.decode('big5')
    
    # 將解碼後的內容轉換成 DataFrame
    df = pd.read_csv(io.StringIO(decoded_content))
    return df
    
# 2. 自動抓取最新價格
def get_price(ticker):
    ticker_str = f"{ticker}.TW" if str(ticker) != "00973B" else "00973B.TW"
    try:
        data = yf.Ticker(ticker_str).history(period="1d")
        return data['Close'].iloc[-1]
    except:
        return None

st.title("📊 個人投資儀表板")

df = load_data()
df['現價'] = df['股票代號'].apply(get_price)
df['市值'] = df['持有股數'] * df['現價']
df['損益'] = df['市值'] - (df['持有股數'] * df['平均成本'])
df['報酬率'] = (df['損益'] / (df['持有股數'] * df['平均成本'])) * 100

# 顯示總覽
col1, col2 = st.columns(2)
col1.metric("總市值", f"NT$ {df['市值'].sum():,.0f}")
col2.metric("總損益", f"NT$ {df['損益'].sum():,.0f}")

# 帳戶篩選
account = st.selectbox("選擇帳戶", ["全部"] + list(df['券商'].unique()))
view_df = df if account == "全部" else df[df['券商'] == account]

# 顯示表格
st.dataframe(view_df[['股票名稱', '持有股數', '現價', '平均成本', '市值', '報酬率']])

# 視覺化
fig = px.pie(view_df, values='市值', names='股票名稱', title='資產配置比例')
st.plotly_chart(fig)
