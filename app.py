import streamlit as st
import google.generativeai as genai
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json, re, pandas as pd
from datetime import datetime

# --- 1. KẾT NỐI GOOGLE SHEETS THÔNG MINH ---
try:
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    # Tự động chọn: Online dùng Secrets, Local dùng file key.json
    if "google_service_account" in st.secrets:
        creds_info = st.secrets["google_service_account"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_info, scope)
    else:
        creds = ServiceAccountCredentials.from_json_keyfile_name("key.json", scope)
        
    client_sheet = gspread.authorize(creds)
    sheet = client_sheet.open("HaWritingApp_Database").sheet1
except Exception as e:
    st.error(f"Lỗi kết nối Sheets: {e}")

# --- 2. CẤU HÌNH AI GEMINI ---
try:
    # Lấy API Key từ Secrets
    API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=API_KEY)
    # Dùng model ổn định nhất để tránh lỗi 404
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    st.error(f"Lỗi cấu hình AI: {e}")

# --- 3. THIẾT LẬP GIAO DIỆN ---
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
                    prompt = f"Chấm bài Flyers cho {name}. Đề: {topic}. Bài: {writing}. Trả về JSON: {{\"score\":\"X/5 Shields\", \"annotated\":\"HTML\", \"feedback\":\"văn bản\"}}"
                    response = model.generate_content(prompt)
                    data = json.loads(re.search(r'\{.*\}', response.text, re.DOTALL).group().replace('\n', ' '))
                    
                    st.balloons()
                    st.markdown(f"### 🏆 Kết quả: {data['score']}")
                    st.markdown(f'<div style="background-color:#1E1E1E;padding:20px;border-radius:10px;">{data["annotated"]}</div>', unsafe_allow_html=True)
                    st.info(data['feedback'])
                    
                    sheet.append_row([datetime.now().strftime("%d/%m/%Y %H:%M:%S"), name, topic, writing, data['score'], data['feedback']])
                    st.toast("Đã lưu vào Sheets! ✅")
                except Exception as e:
                    st.error(f"Lỗi: {e}")
else:
    st.title("📊 Dashboard Cô Hà")
    if st.sidebar.text_input("Mật khẩu:", type="password") == "CoHa9.0":
        df = pd.DataFrame(sheet.get_all_records())
        st.metric("Tổng bài chấm", len(df))
        st.dataframe(df, use_container_width=True)
