import streamlit as st
from google import genai
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json, re, pandas as pd
from datetime import datetime

# --- 1. KẾT NỐI SHEETS THÔNG MINH ---
try:
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    # Tự động detect môi trường
    if "google_service_account" in st.secrets:
        creds_dict = st.secrets["google_service_account"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    else:
        creds = ServiceAccountCredentials.from_json_keyfile_name("key.json", scope)
        
    client_sheet = gspread.authorize(creds)
    sheet = client_sheet.open("HaWritingApp_Database").sheet1
except Exception as e:
    st.error(f"Lỗi kết nối Sheets: {e}")

# --- 2. CẤU HÌNH AI ---
API_KEY = st.secrets["GEMINI_API_KEY"] if "GEMINI_API_KEY" in st.secrets else "Dán_Key_Local_Của_Hà"
client_ai = genai.Client(api_key=API_KEY)

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
                    prompt = f"Bạn là cô Hà chấm Flyers cho {name}. Đề: {topic}. Bài: {writing}. Trả về JSON: {{\"score\":\"X/5 Shields\", \"annotated\":\"HTML\", \"feedback\":\"văn bản\"}}"
                    # Dùng model ổn định nhất trên Cloud
                    response = client_ai.models.generate_content(model='gemini-1.5-flash', contents=prompt)
                    data = json.loads(re.search(r'\{.*\}', response.text, re.DOTALL).group())
                    
                    st.balloons()
                    st.markdown(f"### 🏆 Kết quả: {data['score']}")
                    st.markdown(f'<div style="background-color:#1E1E1E;padding:20px;border-radius:12px;">{data["annotated"]}</div>', unsafe_allow_html=True)
                    st.info(data['feedback'])
                    
                    # Đổ dữ liệu về Sheets
                    sheet.append_row([datetime.now().strftime("%d/%m/%Y %H:%M:%S"), name, topic, writing, data['score'], data['feedback']])
                    st.toast("Đã lưu vào Sheets! ✅")
                except Exception as e:
                    st.error(f"Lỗi: {e}")
