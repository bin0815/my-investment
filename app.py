import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px

st.set_page_config(page_title="投資組合儀表板", layout="wide")

# 1. 載入資料
@st.cache_data
def load_data():
    # 讀取檔案
    df = pd.read_csv("invest_data.csv", encoding='utf-8-sig')
    
    # 清洗數字欄位：移除逗號與引號，轉換為數字
    cols_to_clean = ['持有股數', '平均成本', '目前市價', '持倉市值']
    for col in cols_to_clean:
        if df[col].dtype == 'object':
            df[col] = df[col].astype(str).str.replace(',', '').str.replace('"', '').astype(float)
            
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
