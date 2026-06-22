import streamlit as st
import pandas as pd
import io

@st.cache_data
def load_data():
    # 1. 以二進位模式開啟檔案，避免任何編碼轉換衝突
    with open("invest_data.csv", "rb") as f:
        raw_data = f.read()
    
    # 2. 嘗試用 utf-8-sig 解碼，失敗則改用 big5
    try:
        data = raw_data.decode('utf-8-sig')
    except:
        data = raw_data.decode('big5')
    
    # 3. 使用 StringIO 將數據轉為虛擬檔案，再由 pandas 讀取
    df = pd.read_csv(io.StringIO(data))
    
    # 4. 清洗數字欄位：移除逗號與引號，確保運算正常
    cols_to_clean = ['持有股數', '平均成本', '目前市價', '持倉市值']
    for col in cols_to_clean:
        if col in df.columns:
            # 確保內容為字串後，移除逗號、引號並轉換為浮點數
            df[col] = df[col].astype(str).str.replace(',', '').str.replace('"', '').astype(float)
            
    return df

# 1. 修正 get_price 函數，自動處理代號後綴
def get_price(ticker):
    ticker_str = str(ticker)
    # 針對台股加後綴
    query = f"{ticker_str}.TW" if not ticker_str.endswith(".TW") else ticker_str
    try:
        data = yf.Ticker(query).history(period="1d")
        if not data.empty:
            return data['Close'].iloc[-1]
        return 0 # 若抓不到，回傳 0 以免程式崩潰
    except:
        return 0

# 2. 修改主邏輯，確保計算時不會出現 None
df = load_data()
# 確保代號轉為字串
df['股票代號'] = df['股票代號'].astype(str)
df['現價'] = df['股票代號'].apply(get_price)

# 如果市價抓不到，預設補上您 CSV 裡的「目前市價」作為備援
df['現價'] = df['現價'].replace(0, pd.NA).fillna(df['目前市價'])

# 重新計算
df['市值'] = df['持有股數'] * df['現價']
df['損益'] = df['市值'] - (df['持有股數'] * df['平均成本'])
df['報酬率'] = (df['損益'] / (df['持有股數'] * df['平均成本'])) * 100


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
