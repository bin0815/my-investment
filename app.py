import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import io

st.set_page_config(page_title="個人投資儀表板", layout="wide")

# 1. 資料讀取函式
@st.cache_data(ttl=0)
def load_data():
    sheet_id = "1WSjgIJLVe1G1pamo9EhjngxTfRJVvFbLowi4aJ-4kDM"
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet=工作表1"
    
    response = requests.get(url)
    response.encoding = 'utf-8'
    df_raw = pd.read_csv(io.StringIO(response.text))
    
    # 股票：假設在左側 (A-H)，移除空列
    stocks = df_raw.iloc[:, 0:8].dropna(how='all')
    
    # 現金：假設在 Q-R 欄 (Python index 16, 17)
    cash = df_raw.iloc[:, 16:18].dropna(how='all')
    cash.columns = ['帳戶', '金額']
    
    return stocks, cash

@st.cache_data(ttl=0)
def load_history():
    sheet_id = "1WSjgIJLVe1G1pamo9EhjngxTfRJVvFbLowi4aJ-4kDM"
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet=History"
    df = pd.read_csv(url)
    df.columns = df.columns.str.strip() # 清理標題空白
    df['日期'] = pd.to_datetime(df['日期'])
    df['總市值'] = pd.to_numeric(df['總市值'], errors='coerce')
    return df

# 2. 資料載入與計算
stocks, cash = load_data()

# 股票欄位清理
for col in ['持有股數', '平均成本', '目前市價']:
    if col in stocks.columns:
        stocks[col] = pd.to_numeric(stocks[col].astype(str).str.replace(',', ''), errors='coerce').fillna(0)

stocks['市值'] = stocks['持有股數'] * stocks['目前市價']
stocks['損益'] = stocks['市值'] - (stocks['持有股數'] * stocks['平均成本'])
cash['金額'] = pd.to_numeric(cash['金額'].astype(str).str.replace(',', ''), errors='coerce').fillna(0)

total_stock_value = stocks['市值'].sum()
total_cash = cash['金額'].sum()

# 3. 介面顯示
st.title("📊 個人投資儀表板")

col1, col2, col3 = st.columns(3)
col1.metric("股票總市值", f"NT$ {total_stock_value:,.0f}")
col2.metric("現金水位", f"NT$ {total_cash:,.0f}")
col3.metric("總資產", f"NT$ {total_stock_value + total_cash:,.0f}")

st.divider()

# 表格區
tab1, tab2 = st.tabs(["持倉明細", "資產趨勢"])

with tab1:
    st.subheader("股票持倉")
    st.dataframe(stocks)
    st.subheader("現金部位")
    st.dataframe(cash)
    
    # 圓餅圖
    asset_data = pd.concat([
        stocks[['股票名稱', '市值']].rename(columns={'股票名稱': '項目'}),
        cash.rename(columns={'帳戶': '項目', '金額': '市值'})
    ])
    fig = px.pie(asset_data, values='市值', names='項目', title='總資產配置比例')
    st.plotly_chart(fig)

with tab2:
    st.subheader("資產成長趨勢")
    try:
        history_data = load_history()
        
        # --- 新增：將日期轉為純日期格式 (去除小時分鐘) ---
        history_data['日期'] = pd.to_datetime(history_data['日期']).dt.strftime('%Y-%m-%d')
        
        # 繪圖
        fig_history = px.line(history_data, x='日期', y='總市值', title="總資產市值歷史走勢")
        
        # --- 新增：固定 X 軸顯示設定 ---
        fig_history.update_xaxes(
            type='category',  # 強制將 X 軸視為類別(日期)，這樣就不會顯示小時
            tickmode='auto'   # 讓系統自動根據資料量調整顯示密度
        )
        
        st.plotly_chart(fig_history, use_container_width=True)
        
    except Exception as e:
        st.info("尚無歷史記錄或讀取發生錯誤。")
