import streamlit as st
from google import genai
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
import re
import pandas as pd
from datetime import datetime

# --- 1. KẾT NỐI GOOGLE SHEETS ---
try:
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    
    # Bảo mật: Ưu tiên dùng Secrets khi online, dùng file key.json khi chạy local
    if "gcp_service_account" in st.secrets:
        creds_dict = dict(st.secrets["gcp_service_account"])
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    else:
        creds = ServiceAccountCredentials.from_json_keyfile_name("key.json", scope)
        
    client_sheet = gspread.authorize(creds)
    sheet = client_sheet.open("HaWritingApp_Database").sheet1
except Exception as e:
    st.error(f"Lỗi kết nối Sheets: {e}")

# --- 2. CẤU HÌNH AI GEMINI ---
# Bảo mật API Key qua Secrets
API_KEY = st.secrets["GEMINI_API_KEY"] if "GEMINI_API_KEY" in st.secrets else "AIzaSy..." 
client_ai = genai.Client(api_key=API_KEY)

# --- 3. THIẾT LẬP GIAO DIỆN ---
st.set_page_config(page_title="Flyers Grader", page_icon="✍️", layout="wide")

st.sidebar.title("💎 Cổng Điều Hướng")
role = st.sidebar.selectbox("Bạn là ai?", ["Học sinh nộp bài", "Cô Hà quản lý"])

# --- 4. CHẾ ĐỘ HỌC SINH NỘP BÀI ---
if role == "Học sinh nộp bài":
    st.title("Flyers Writing Grader - Cô Hà ✍️")
    st.markdown("---")
    
    name = st.text_input("Tên của con:")
    topic = st.text_input("Đề bài (Topic):")
    writing = st.text_area("Bài viết của con:", height=250)

    if st.button("Gửi bài cho Cô Hà 🚀"):
        if name and writing:
            with st.spinner("Cô Hà đang xem kỹ bài..."):
                try:
                    prompt = f"""
                    Bạn là cô Hà giáo viên tiếng Anh chấm Flyers cho {name}. Đề: {topic}. Bài: {writing}.
                    NHIỆM VỤ:
                    1. Annotated: Sửa lỗi chính tả, ngữ pháp, viết hoa. Dùng HTML <strike> và <span>.
                    2. Feedback: 3 mục (Tổng kết lỗi, Level up, Khích lệ).
                    TRẢ VỀ JSON: {{"score": "X/5 Shields", "annotated": "HTML", "feedback": "text"}}
                    """
                    # SỬA LỖI TẠI ĐÂY: Đổi gemini-2.5-flash thành gemini-1.5-flash
                    response = client_ai.models.generate_content(model='gemini-1.5-flash', contents=prompt)
                    
                    match = re.search(r'\{.*\}', response.text, re.DOTALL)
                    if match:
                        data = json.loads(match.group())
                        st.balloons()
                        st.markdown(f"### 🏆 Kết quả của {name}: {data.get('score')}")
                        st.markdown(f'''<div style="background-color: #1E1E1E; color: #DCDCDC; padding: 25px; border-radius: 12px;">{data.get('annotated')}</div>''', unsafe_allow_html=True)
                        st.info(data.get('feedback'))
                        
                        now = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                        sheet.append_row([now, name, topic, writing, data.get('score'), data.get('feedback')])
                        st.toast("Đã lưu bài thành công! ✅")
                except Exception as e:
                    st.error(f"Lỗi chấm bài: {e}")
        else:
            st.warning("Hà điền đủ thông tin nha!")

# --- 5. CHẾ ĐỘ DASHBOARD ---
else:
    st.title("📊 Dashboard Quản Lý Lớp Học")
    password = st.sidebar.text_input("Nhập mật khẩu giáo viên:", type="password")
    
    # Bảo mật mật khẩu qua Secrets
    MASTER_PASSWORD = st.secrets["TEACHER_PASSWORD"] if "TEACHER_PASSWORD" in st.secrets else "CoHa9.0"
    
    if password == MASTER_PASSWORD:
        st.success("Chào Hà nhé! ❤️")
        try:
            data_rows = sheet.get_all_records()
            if data_rows:
                df = pd.DataFrame(data_rows)
                st.dataframe(df, use_container_width=True)
            else:
                st.info("Chưa có bài nộp nào.")
        except Exception as e:
            st.error(f"Lỗi Dashboard: {e}")
