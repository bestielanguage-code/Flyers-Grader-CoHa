import streamlit as st
from google import genai
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json, re, pandas as pd
from datetime import datetime

# --- 1. KẾT NỐI SHEETS (Dùng Secrets) ---
try:
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_dict = st.secrets["gcp_service_account"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client_sheet = gspread.authorize(creds)
    sheet = client_sheet.open("HaWritingApp_Database").sheet1
except Exception as e:
    st.error(f"Lỗi Sheets: {e}")

# --- 2. CẤU HÌNH AI (Dùng Model ổn định nhất) ---
client_ai = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])

# --- 3. GIAO DIỆN ---
st.set_page_config(page_title="Flyers Grader", layout="wide")
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
                    Sửa lỗi dùng <strike style='color:#FF6B6B;'>sai</strike> <span style='color:#4ECDC4;font-weight:bold;'>đúng</span>. 
                    Phần feedback 3 mục: Tổng kết lỗi, Level Up, Khích lệ. 
                    TRẢ VỀ JSON: {{"score":"X/5 Shields", "annotated":"HTML", "feedback":"văn bản 3 mục"}}"""
                    
                    # SỬA MODEL Ở ĐÂY ĐỂ HẾT LỖI 404
                    response = client_ai.models.generate_content(model='gemini-1.5-flash', contents=prompt)
                    data = json.loads(re.search(r'\{.*\}', response.text, re.DOTALL).group())
                    
                    st.balloons()
                    st.markdown(f"### 🏆 Kết quả: {data['score']}")
                    st.markdown(f'<div style="background-color:#1E1E1E;padding:20px;border-radius:10px;">{data["annotated"]}</div>', unsafe_allow_html=True)
                    st.info(data['feedback'])
                    
                    sheet.append_row([datetime.now().strftime("%d/%m/%Y %H:%M:%S"), name, topic, writing, data['score'], data['feedback']])
                    st.toast("Đã lưu vào Sheets! ✅")
                except Exception as e:
                    st.error(f"Lỗi: {e}")
