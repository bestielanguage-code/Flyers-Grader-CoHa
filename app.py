import streamlit as st
from google import genai
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json, re, pandas as pd
from datetime import datetime

# --- 1. KẾT NỐI SHEETS ---
try:
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_dict = st.secrets["gcp_service_account"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client_sheet = gspread.authorize(creds)
    sheet = client_sheet.open("HaWritingApp_Database").sheet1
except Exception as e:
    st.error(f"Lỗi Sheets: {e}")

# --- 2. AI CONFIG (Dùng model mới nhất) ---
client_ai = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])

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
                    # Ép AI trả về JSON chuẩn, không được trả về List
                    prompt = f"""Bạn là cô Hà chấm Flyers cho {name}. Đề: {topic}. Bài: {writing}. 
                    Sửa lỗi dùng <strike>sai</strike> <span>đúng</span>. 
                    Phần feedback viết 3 mục: 1. Tổng kết lỗi, 2. Level Up, 3. Khích lệ. 
                    CHỈ TRẢ VỀ JSON: {{"score":"X/5 Shields", "annotated":"HTML", "feedback":"văn bản thuần"}}"""
                    
                    # ĐỔI TÊN MODEL Ở ĐÂY
                    response = client_ai.models.generate_content(model='gemini-2.0-flash-lite-001', contents=prompt)
                    data = json.loads(re.search(r'\{.*\}', response.text, re.DOTALL).group().replace('\n', ' '))
                    
                    st.balloons()
                    st.markdown(f"### 🏆 Kết quả của {name}: {data['score']}")
                    st.markdown(f'<div style="background-color:#1E1E1E;padding:20px;border-radius:10px;">{data["annotated"]}</div>', unsafe_allow_html=True)
                    st.info(data['feedback'])
                    
                    sheet.append_row([datetime.now().strftime("%d/%m/%Y %H:%M:%S"), name, topic, writing, data['score'], data['feedback']])
                    st.toast("Đã lưu vào Sheets! ✅")
                except Exception as e:
                    st.error(f"Lỗi chấm bài: {e}")
