import streamlit as st
from google import genai
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json, re, pandas as pd
from datetime import datetime

# --- 1. KẾT NỐI SHEETS THÔNG MINH ---
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
    st.error(f"Lỗi Sheets: {e}")

# --- 2. CẤU HÌNH AI (Dùng Model ổn định tuyệt đối) ---
api_key = st.secrets["GEMINI_API_KEY"] if "GEMINI_API_KEY" in st.secrets else "Dán_API_Key_Vào_Đây"
client_ai = genai.Client(api_key=api_key)

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
            with st.spinner("Cô Hà đang xem kỹ bài..."):
                try:
                    prompt = f"""Bạn là cô Hà chấm Flyers cho {name}. Đề: {topic}. Bài: {writing}. 
                    1. Annotated: Sửa lỗi dùng <strike style='color:#FF6B6B;'>sai</strike> <span style='color:#4ECDC4;font-weight:bold;'>đúng</span>. 
                    2. Feedback: Viết ngắn 3 mục: Tổng kết lỗi, Level Up, Khích lệ. 
                    CHỈ TRẢ VỀ JSON: {{"score":"X/5 Shields", "annotated":"HTML", "feedback":"văn bản thuần"}}"""
                    
                    # DÙNG MODEL NÀY ĐỂ HẾT LỖI 404
                    response = client_ai.models.generate_content(model='gemini-1.5-flash-8b', contents=prompt)
                    data = json.loads(re.search(r'\{.*\}', response.text, re.DOTALL).group().replace('\n', ' '))
                    
                    st.balloons()
                    st.markdown(f"### 🏆 Kết quả của {name}: {data['score']}")
                    st.markdown(f'<div style="background-color:#1E1E1E;padding:25px;border-radius:12px;line-height:2;">{data["annotated"]}</div>', unsafe_allow_html=True)
                    st.info(data['feedback'])
                    
                    sheet.append_row([datetime.now().strftime("%d/%m/%Y %H:%M:%S"), name, topic, writing, data['score'], data['feedback']])
                    st.toast("Đã nộp bài thành công! ✅")
                except Exception as e:
                    st.error(f"Lỗi AI: {e}")
else:
    # Dashboard cho Hà
    st.title("📊 Dashboard")
    password = st.sidebar.text_input("Mật khẩu:", type="password")
    correct_pass = st.secrets["TEACHER_PASSWORD"] if "TEACHER_PASSWORD" in st.secrets else "CoHa9.0"
    if password == correct_pass:
        df = pd.DataFrame(sheet.get_all_records())
        st.metric("Tổng bài chấm", len(df))
        st.dataframe(df, use_container_width=True)
