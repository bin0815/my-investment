import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px
import io

st.set_page_config(page_title="個人投資儀表板", layout="wide")

# 1. 載入資料
@st.cache_data
def load_data():
    with open("invest_data.csv", "rb") as f:
        content = f.read()
    try:
        decoded_content = content.decode('utf-8-sig')
    except:
        decoded_content = content.decode('big5')
    
    df = pd.read_csv(io.StringIO(decoded_content))
    
    # 清洗數值欄位
    cols_to_clean = ['持有股數', '平均成本', '目前市價', '持倉市值']
    for col in cols_to_clean:
        if col in df.columns:
            df[col] = df[col].astype(str).str.replace(',', '').str.replace('"', '').astype(float)
    return df

# 2. 初始化與處理
df = load_data()

# 確保 '現價' 欄位存在，先給預設值
if '現價' not in df.columns:
    df['現價'] = df['目前市價']
else:
    # 若有抓取邏輯，確保它不會報錯
    df['現價'] = df['現價'].fillna(df['目前市價'])

# 計算損益
df['市值'] = df['持有股數'] * df['現價']
df['損益'] = df['市值'] - (df['持有股數'] * df['平均成本'])
df['報酬率'] = (df['損益'] / (df['持有股數'] * df['平均成本'])) * 100

# 3. 儀表板顯示
st.title("📊 個人投資儀表板")

col1, col2 = st.columns(2)
col1.metric("總市值", f"NT$ {df['市值'].sum():,.0f}")
col2.metric("總損益", f"NT$ {df['損益'].sum():,.0f}")

# 帳戶篩選
account = st.selectbox("選擇帳戶", ["全部"] + list(df['券商'].unique()))
view_df = df if account == "全部" else df[df['券商'] == account]

# 顯示表格
st.dataframe(view_df[['股票名稱', '持有股數', '現價', '平均成本', '市值', '報酬率']])

# 視覺化
if not view_df.empty and view_df['市值'].sum() > 0:
    fig = px.pie(view_df, values='市值', names='股票名稱', title='資產配置比例')
    st.plotly_chart(fig)
