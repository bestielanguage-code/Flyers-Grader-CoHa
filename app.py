import streamlit as st
from google import genai
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
import re
import pandas as pd
from datetime import datetime

# --- 1. KẾT NỐI SHEETS (Thông minh) ---
try:
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    # Tự động chọn: Online dùng Secrets, Local dùng file
    if "gcp_service_account" in st.secrets:
        creds_dict = st.secrets["gcp_service_account"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    else:
        creds = ServiceAccountCredentials.from_json_keyfile_name("key.json", scope)
        
    client_sheet = gspread.authorize(creds)
    sheet = client_sheet.open("HaWritingApp_Database").sheet1
except Exception as e:
    st.error(f"Lỗi kết nối Sheets: {e}")

# --- 2. CẤU HÌNH AI (Fix model 404) ---
API_KEY = st.secrets["GEMINI_API_KEY"] if "GEMINI_API_KEY" in st.secrets else "Dán_API_Key_Của_Hà_Vào_Đây"
client_ai = genai.Client(api_key=API_KEY)

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
                    1. Annotated: Sửa lỗi dùng <strike style='color:#FF6B6B;'>sai</strike> <span style='color:#4ECDC4;font-weight:bold;'>đúng</span>. 
                    2. Feedback: Viết ngắn gọn 3 mục: TỔNG KẾT LỖI, LEVEL UP, KHÍCH LỆ. 
                    QUAN TRỌNG: Feedback là văn bản thuần, không phải danh sách.
                    TRẢ VỀ JSON: {{"score":"X/5 Shields", "annotated":"HTML", "feedback":"văn bản"}}"""
                    
                    # Dùng model này để không bao giờ bị 404
                    response = client_ai.models.generate_content(model='gemini-1.5-flash', contents=prompt)
                    match = re.search(r'\{.*\}', response.text, re.DOTALL)
                    if match:
                        data = json.loads(match.group().replace('\n', ' '))
                        st.balloons()
                        st.markdown(f"### 🏆 Kết quả của {name}: {data['score']}")
                        st.markdown(f'<div style="background-color:#1E1E1E;padding:25px;border-radius:12px;line-height:2;">{data["annotated"]}</div>', unsafe_allow_html=True)
                        st.info(data['feedback'])
                        
                        # Đổ dữ liệu về Sheets
                        sheet.append_row([datetime.now().strftime("%d/%m/%Y %H:%M:%S"), name, topic, writing, data['score'], data['feedback']])
                        st.toast("Đã lưu vào Sheets! ✅")
                except Exception as e:
                    st.error(f"Lỗi: {e}")
