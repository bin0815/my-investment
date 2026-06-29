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
    df.columns = df.columns.str.strip() 
    df['日期'] = pd.to_datetime(df['日期'])
    df['總市值'] = pd.to_numeric(df['總市值'], errors='coerce')
    return df

# 2. 資料載入與計算 (此段請替換原有的計算部分)
stocks, cash = load_data()

# 股票欄位清理
for col in ['持有股數', '平均成本', '目前市價']:
    if col in stocks.columns:
        stocks[col] = pd.to_numeric(stocks[col].astype(str).str.replace(',', ''), errors='coerce').fillna(0)

# 計算市值與損益
stocks['市值'] = stocks['持有股數'] * stocks['目前市價']
stocks['成本'] = stocks['持有股數'] * stocks['平均成本']
stocks['損益'] = stocks['市值'] - stocks['成本']

# 現金處理
cash['金額'] = pd.to_numeric(cash['金額'].astype(str).str.replace(',', ''), errors='coerce').fillna(0)

# 計算總計數值
total_stock_value = stocks['市值'].sum()
total_cost = stocks['成本'].sum()
total_cash = cash['金額'].sum()
total_gain_loss = stocks['損益'].sum()

# 【新增】計算總報酬率 (%)
# 若總成本為0，則報酬率為0
total_roi = (total_gain_loss / total_cost * 100) if total_cost != 0 else 0

# 3. 介面顯示
st.title("📊 個人投資儀表板")

# 四欄位佈局
col1, col2, col3, col4 = st.columns(4)
col1.metric("股票總市值", f"NT$ {total_stock_value:,.0f}")
col2.metric("現金水位", f"NT$ {total_cash:,.0f}")
# 在總損益指標後方加上報酬率百分比
col3.metric("總損益", f"NT$ {total_gain_loss:,.0f}", f"{total_roi:.2f}%") 
col4.metric("總資產", f"NT$ {total_stock_value + total_cash:,.0f}")
# 表格區
tab1, tab2 = st.tabs(["持倉明細", "資產趨勢"])

with tab1:
    st.subheader("股票持倉")
    display_cols = ['股票名稱', '持有股數', '平均成本', '目前市價', '市值', '損益']
    st.dataframe(stocks[display_cols], use_container_width=True)
    
    st.subheader("現金部位")
    st.dataframe(cash, use_container_width=True)
    
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
        history_data['日期'] = pd.to_datetime(history_data['日期']).dt.strftime('%Y-%m-%d')
        fig_history = px.line(history_data, x='日期', y='總市值', title="總資產市值歷史走勢")
        fig_history.update_xaxes(type='category', tickmode='auto')
        st.plotly_chart(fig_history, use_container_width=True)
    except Exception as e:
        st.info("尚無歷史記錄或讀取發生錯誤。")
