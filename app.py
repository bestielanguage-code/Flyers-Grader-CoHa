import streamlit as st
from google import genai
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
import re
import pandas as pd
from datetime import datetime

# --- 1. KẾT NỐI GOOGLE SHEETS (An toàn) ---
try:
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_dict = st.secrets["gcp_service_account"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client_sheet = gspread.authorize(creds)
    sheet = client_sheet.open("HaWritingApp_Database").sheet1
except Exception as e:
    st.error(f"Lỗi kết nối Sheets: {e}. Hà kiểm tra lại mục Secrets nhé!")

# --- 2. CẤU HÌNH AI GEMINI ---
API_KEY = st.secrets["GEMINI_API_KEY"]
client_ai = genai.Client(api_key=API_KEY)

# --- 3. GIAO DIỆN ---
st.set_page_config(page_title="Flyers Grader & Dashboard", page_icon="✍️", layout="wide")
st.sidebar.title("💎 Cổng Điều Hướng")
role = st.sidebar.selectbox("Bạn là ai?", ["Học sinh nộp bài", "Cô Hà quản lý"])

if role == "Học sinh nộp bài":
    st.title("Flyers Writing Grader - Cô Hà ✍️")
    name = st.text_input("Tên của con:")
    topic = st.text_input("Đề bài:")
    writing = st.text_area("Bài viết của con:", height=250)

    if st.button("Gửi bài cho Cô Hà 🚀"):
        if name and writing:
            with st.spinner("Cô Hà đang xem kỹ bài..."):
                try:
                    prompt = f"""Bạn là cô Hà chấm Flyers cho {name}. Đề: {topic}. Bài: {writing}.
                    1. Annotated: Sửa lỗi dùng <strike style='color:#FF6B6B;'>sai</strike> <span style='color:#4ECDC4;font-weight:bold;'>đúng</span>.
                    2. Feedback: Viết ngắn gọn 3 mục: TỔNG KẾT LỖI & GIẢI PHÁP, LEVEL UP, KHÍCH LỆ.
                    TRẢ VỀ JSON: {{"score":"X/5 Shields", "annotated":"HTML sửa bài", "feedback":"Lời dặn 3 mục"}}"""
                    
                    # Dùng model ổn định nhất hiện tại
                    response = client_ai.models.generate_content(model='gemini-1.5-flash', contents=prompt)
                    match = re.search(r'\{.*\}', response.text, re.DOTALL)
                    if match:
                        data = json.loads(match.group().replace('\n', ' ').replace('\r', ''))
                        st.balloons()
                        st.write(f"### 🏆 Kết quả của {name}: {data['score']}")
                        st.markdown(f'<div style="background-color:#1E1E1E;padding:25px;border-radius:12px;">{data["annotated"]}</div>', unsafe_allow_html=True)
                        st.info(data['feedback'])
                        
                        # Lưu vào Sheets
                        now = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                        sheet.append_row([now, name, topic, writing, data['score'], data['feedback']])
                        st.toast("Đã lưu bài thành công! ✅")
                except Exception as e:
                    st.error(f"Lỗi chấm bài: {e}")
else:
    # --- DASHBOARD CHO HÀ ---
    st.title("📊 Dashboard Cô Hà")
    password = st.sidebar.text_input("Mật khẩu:", type="password")
    if password == st.secrets["TEACHER_PASSWORD"]:
        data_rows = sheet.get_all_records()
        if data_rows:
            df = pd.DataFrame(data_rows)
            st.metric("Tổng số bài đã chấm", len(df))
            st.bar_chart(df['Student Name'].value_counts())
            st.dataframe(df, use_container_width=True)
