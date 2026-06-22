import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import io

st.set_page_config(page_title="個人投資儀表板", layout="wide")

# 1. 強健的數據讀取函式
@st.cache_data(ttl=600)
def load_data():
    sheet_id = "1WSjgIJLVe1G1pamo9EhjngxTfRJVvFbLowi4aJ-4kDM"
    sheet_name = "工作表1"
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={sheet_name}"
    
    response = requests.get(url)
    response.encoding = 'utf-8'
    df = pd.read_csv(io.StringIO(response.text))
    
    # 清除欄位名稱前後的空格
    df.columns = df.columns.str.strip()
    
    # 強制將關鍵欄位轉為數字，無法轉換者設為 0
    cols = ['持有股數', '平均成本', '目前市價', '持倉市值']
    for col in cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', '').str.replace('"', ''), errors='coerce').fillna(0)
    return df

# 2. 數據載入與計算
df = load_data()

# 計算邏輯 (確保不為空)
if not df.empty:
    df['市值'] = df['持有股數'] * df['目前市價']
    df['損益'] = df['市值'] - (df['持有股數'] * df['平均成本'])

# 3. 介面顯示
st.title("📊 個人投資儀表板")

# 帳戶篩選
accounts = ["全部"] + list(df['券商'].unique())
account = st.selectbox("選擇帳戶", accounts)
view_df = df if account == "全部" else df[df['券商'] == account]

# 顯示指標
col1, col2 = st.columns(2)
col1.metric("總市值", f"NT$ {view_df['市值'].sum():,.0f}")
col2.metric("總損益", f"NT$ {view_df['損益'].sum():,.0f}")

# 顯示表格
st.dataframe(view_df[['股票名稱', '持有股數', '目前市價', '平均成本', '市值', '報酬率']])

# 4. 圖表繪製 (增加防呆機制)
if not view_df.empty and '市值' in view_df.columns and view_df['市值'].sum() > 0:
    fig = px.pie(view_df, values='市值', names='股票名稱', title='資產配置比例')
    st.plotly_chart(fig)
else:
    st.info("目前選擇的數據不足以顯示圓餅圖。")
