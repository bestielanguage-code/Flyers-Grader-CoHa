import streamlit as st
import google.generativeai as openai
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
import re
import pandas as pd
from datetime import datetime

# --- 1. KẾT NỐI GOOGLE SHEETS ---
try:
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    # Tự động chọn: Online dùng Secrets, Local dùng file key.json
    if "gcp_service_account" in st.secrets:
        creds_info = st.secrets["gcp_service_account"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_info, scope)
    else:
        creds = ServiceAccountCredentials.from_json_keyfile_name("key.json", scope)
        
    client_sheet = gspread.authorize(creds)
    sheet = client_sheet.open("HaWritingApp_Database").sheet1
except Exception as e:
    st.error(f"Lỗi kết nối Sheets: {e}")

# --- 2. CẤU HÌNH AI GEMINI ---
API_KEY = st.secrets["GEMINI_API_KEY"]
openai.configure(api_key=API_KEY)
# Dùng model ổn định nhất hiện nay
model = openai.GenerativeModel('gemini-1.5-flash')

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
                    prompt = f"""
                    Bạn là cô Hà chấm Flyers cho {name}. Đề: {topic}. Bài: {writing}.
                    Sửa lỗi dùng <strike style='color: #FF6B6B;'>sai</strike> <span style='color: #4ECDC4; font-weight: bold;'>đúng</span>.
                    Feedback viết 3 mục: Tổng kết lỗi, Level Up, Khích lệ.
                    TRẢ VỀ JSON CHUẨN: {{"score":"X/5 Shields", "annotated":"HTML...", "feedback":"Lời dặn..."}}
                    """
                    response = model.generate_content(prompt)
                    # Xử lý text để lấy JSON sạch
                    clean_text = re.search(r'\{.*\}', response.text, re.DOTALL).group()
                    data = json.loads(clean_text)
                    
                    st.balloons()
                    st.markdown(f"### 🏆 Kết quả của {name}: {data['score']}")
                    st.markdown(f'<div style="background-color: #1E1E1E; padding: 20px; border-radius: 10px;">{data["annotated"]}</div>', unsafe_allow_html=True)
                    st.info(data['feedback'])
                    
                    # Lưu vào Sheets
                    sheet.append_row([datetime.now().strftime("%d/%m/%Y %H:%M:%S"), name, topic, writing, data['score'], data['feedback']])
                    st.toast("Đã nộp bài thành công! ✅")
                except Exception as e:
                    st.error(f"Lỗi AI: {e}")
