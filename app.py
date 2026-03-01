import streamlit as st
from google import genai
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json, re, pandas as pd
from datetime import datetime

# --- 1. KẾT NỐI SHEETS THÔNG MINH ---
try:
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    # Tự động nhận diện Online/Local
    if "gcp_service_account" in st.secrets:
        creds_dict = st.secrets["gcp_service_account"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    else:
        creds = ServiceAccountCredentials.from_json_keyfile_name("key.json", scope)
    client_sheet = gspread.authorize(creds)
    sheet = client_sheet.open("HaWritingApp_Database").sheet1
except Exception as e:
    st.error(f"Lỗi Sheets: {e}")

# --- 2. CẤU HÌNH AI (Dùng Model ổn định nhất) ---
# CHÚ Ý: Hà đổi tên model thành 'gemini-1.5-flash' hoặc 'gemini-2.0-flash-exp'
API_KEY = st.secrets["GEMINI_API_KEY"] if "GEMINI_API_KEY" in st.secrets else "AIzaSy..."
client_ai = genai.Client(api_key=API_KEY)

# --- 3. GIAO DIỆN ---
st.set_page_config(page_title="Flyers Grader", page_icon="✍️", layout="wide")
role = st.sidebar.selectbox("Bạn là ai?", ["Học sinh nộp bài", "Cô Hà quản lý"])

if role == "Học sinh nộp bài":
    st.title("Flyers Writing Grader - Cô Hà ✍️")
    name = st.text_input("Tên của con:")
    topic = st.text_input("Đề bài:")
    writing = st.text_area("Bài viết của con:", height=250)

    if st.button("Gửi bài cho Cô Hà 🚀"):
        if name and writing:
            with st.spinner("Cô Hà đang chấm bài..."):
                try:
                    prompt = f"""Bạn là cô Hà chấm Flyers cho {name}. Đề: {topic}. Bài: {writing}. 
                    TRẢ VỀ JSON: {{"score":"X/5 Shields", "annotated":"HTML sửa bài", "feedback":"Lời dặn 3 mục"}}"""
                    
                    # SỬA TÊN MODEL CHUẨN Ở ĐÂY (gemini-1.5-flash)
                    response = client_ai.models.generate_content(model='gemini-1.5-flash', contents=prompt)
                    
                    data = json.loads(re.search(r'\{.*\}', response.text, re.DOTALL).group().replace('\n', ' '))
                    st.balloons()
                    st.markdown(f"### 🏆 Kết quả: {data['score']}")
                    st.markdown(f'<div style="background-color:#1E1E1E;padding:25px;border-radius:12px;line-height:2;">{data["annotated"]}</div>', unsafe_allow_html=True)
                    st.info(data['feedback'])
                    
                    # Lưu vào Sheets
                    now = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                    sheet.append_row([now, name, topic, writing, data['score'], data['feedback']])
                    st.toast("Đã nộp bài thành công! ✅")
                except Exception as e:
                    st.error(f"Lỗi: {e}")
else:
    # Dashboard giữ nguyên tính năng cũ của Hà
    st.title("📊 Dashboard Cô Hà")
    password = st.sidebar.text_input("Mật khẩu:", type="password")
    if password == st.secrets.get("TEACHER_PASSWORD", "CoHa9.0"):
        df = pd.DataFrame(sheet.get_all_records())
        st.metric("Tổng bài", len(df))
        st.dataframe(df, use_container_width=True)
