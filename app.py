import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import io

st.set_page_config(page_title="個人投資儀表板", layout="wide")

@st.cache_data(ttl=0)
def load_data():
    sheet_id = "1WSjgIJLVe1G1pamo9EhjngxTfRJVvFbLowi4aJ-4kDM"
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet=工作表1"
    
    response = requests.get(url)
    response.encoding = 'utf-8'
    df_raw = pd.read_csv(io.StringIO(response.text))
    
    # 1. 股票區：我們取前面所有欄位 (假設股票在 A-H 欄)
    # 我們假設股票資料在左側，並移除整行都是空值的列
    stocks = df_raw.iloc[:, 0:8].dropna(how='all')
    
    # 2. 現金區：我們只取 Q 和 R 欄 (Python index 16 和 17)
    # 假設 Q 為'帳戶', R 為'金額'
    cash = df_raw.iloc[:, 16:18].dropna(how='all')
    cash.columns = ['帳戶', '金額'] # 強制重新命名欄位
    
    return stocks, cash

# 載入與計算
stocks, cash = load_data()

# 清理數值欄位 (移除逗號並轉數值)
for col in ['持有股數', '平均成本', '目前市價']:
    if col in stocks.columns:
        stocks[col] = pd.to_numeric(stocks[col].astype(str).str.replace(',', ''), errors='coerce').fillna(0)

stocks['市值'] = stocks['持有股數'] * stocks['目前市價']
stocks['損益'] = stocks['市值'] - (stocks['持有股數'] * stocks['平均成本'])

# 現金處理
cash['金額'] = pd.to_numeric(cash['金額'].astype(str).str.replace(',', ''), errors='coerce').fillna(0)

total_stock_value = stocks['市值'].sum()
total_cash = cash['金額'].sum()

# 介面顯示
st.title("📊 個人投資儀表板")
col1, col2, col3 = st.columns(3)
col1.metric("股票總市值", f"NT$ {total_stock_value:,.0f}")
col2.metric("現金水位", f"NT$ {total_cash:,.0f}")
col3.metric("總資產", f"NT$ {total_stock_value + total_cash:,.0f}")

st.divider()
st.dataframe(stocks)
st.subheader("現金部位")
st.dataframe(cash)

# 圓餅圖：合併顯示
asset_data = pd.concat([
    stocks[['股票名稱', '市值']].rename(columns={'股票名稱': '項目'}),
    cash.rename(columns={'帳戶': '項目', '金額': '市值'})
])
fig = px.pie(asset_data, values='市值', names='項目', title='總資產配置比例')
st.plotly_chart(fig)

# ... 在 app.py 的最下方加入這段 ...

st.divider()
st.subheader("📈 資產成長趨勢")

# 讀取 History 分頁資料
@st.cache_data(ttl=0)
def load_history():
    sheet_id = "1WSjgIJLVe1G1pamo9EhjngxTfRJVvFbLowi4aJ-4kDM"
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet=History"
    df = pd.read_csv(url)
    
    # 1. 強制修正所有欄位名稱的空白，防止「備註 」變成「備註」的格式錯誤
    df.columns = df.columns.str.strip()
    
    # 2. 確保日期轉換成功
    df['日期'] = pd.to_datetime(df['日期'])
    
    # 3. 確保數值是數字
    df['總市值'] = pd.to_numeric(df['總市值'], errors='coerce')
    
    return df

# 在顯示圖表區修改：
try:
    history_data = load_history()
    # 確保這裡的名稱與上面清洗過後的名稱一致
    fig_history = px.line(history_data, x='日期', y='總市值', title="總資產市值歷史走勢")
    st.plotly_chart(fig_history, use_container_width=True)
except Exception as e:
    st.error(f"讀取失敗，錯誤訊息: {e}")
