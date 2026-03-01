import streamlit as st
from google import genai
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
import re
import pandas as pd
from datetime import datetime
import os

# --- 1. KẾT NỐI GOOGLE SHEETS THÔNG MINH ---
try:
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    
    # Kiểm tra xem đang chạy Online hay Local
    if "gcp_service_account" in st.secrets:
        # Chạy Online: Lấy từ Secrets
        creds_dict = st.secrets["gcp_service_account"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    else:
        # Chạy Local: Lấy từ file key.json trong thư mục
        creds = ServiceAccountCredentials.from_json_keyfile_name("key.json", scope)
        
    client_sheet = gspread.authorize(creds)
    sheet = client_sheet.open("HaWritingApp_Database").sheet1
except Exception as e:
    st.error(f"Lỗi kết nối Sheets: {e}")

# --- 2. CẤU HÌNH AI GEMINI (Giữ nguyên model của Hà) ---
API_KEY = st.secrets["GEMINI_API_KEY"] if "GEMINI_API_KEY" in st.secrets else "Dán_API_Key_Vào_Đây_Nếu_Chạy_Local"
client_ai = genai.Client(api_key=API_KEY)

# --- 3. THIẾT LẬP GIAO DIỆN & SIDEBAR ---
st.set_page_config(page_title="Flyers Grader & Dashboard", page_icon="✍️", layout="wide")
st.sidebar.title("💎 Cổng Điều Hướng")
role = st.sidebar.selectbox("Bạn là ai?", ["Học sinh nộp bài", "Cô Hà quản lý"])

# --- 4. CHẾ ĐỘ HỌC SINH NỘP BÀI ---
if role == "Học sinh nộp bài":
    st.title("Flyers Writing Grader - Cô Hà ✍️")
    st.markdown("---")
    name = st.text_input("Tên của con (e.g. Dau, Thỏ):")
    topic = st.text_input("Đề bài (Topic):")
    writing = st.text_area("Bài viết của con:", height=250)

    if st.button("Gửi bài cho Cô Hà 🚀"):
        if name and writing:
            with st.spinner("Cô Hà đang xem kỹ bài..."):
                try:
                    prompt = f"""
                    Bạn là cô Hà giáo viên tiếng Anh chấm Flyers cho {name}. Đề: {topic}. Bài: {writing}.
                    1. Annotated: Sửa TẤT CẢ lỗi chính tả, ngữ pháp, VIẾT HOA, DẤU CÂU.
                       Dùng <strike style='color: #FF6B6B;'>lỗi sai</strike> và <span style='color: #4ECDC4; font-weight: bold;'>đúng</span>.
                    2. Feedback: Viết cực ngắn gọn 3 mục (KHÔNG HTML):
                       - TỔNG KẾT LỖI & GIẢI PHÁP, LEVEL UP, KHÍCH LỆ.
                    TRẢ VỀ JSON: {{"score": "X/5 Shields", "annotated": "HTML", "feedback": "3 mục"}}
                    """
                    # GIỮ NGUYÊN MODEL 2.0 FLASH CỦA HÀ
                    response = client_ai.models.generate_content(model='gemini-2.0-flash', contents=prompt)
                    match = re.search(r'\{.*\}', response.text, re.DOTALL)
                    if match:
                        data = json.loads(match.group().replace('\n', ' ').replace('\r', ''))
                        st.balloons()
                        st.markdown(f"### 🏆 Kết quả của {name}: {data.get('score')}")
                        st.markdown(f'''<div style="background-color: #1E1E1E; color: #DCDCDC; padding: 25px; border-radius: 12px; line-height: 2; font-size: 18px;">{data.get('annotated')}</div>''', unsafe_allow_html=True)
                        st.info(data.get('feedback'))
                        now = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                        sheet.append_row([now, name, topic, writing, data.get('score'), data.get('feedback')])
                        st.toast("Đã lưu bài thành công! ✅")
                except Exception as e:
                    st.error(f"Lỗi chấm bài: {e}")
        else:
            st.warning("Hà điền đủ Tên và Bài viết nha!")

# --- 5. CHẾ ĐỘ DASHBOARD ---
else:
    st.title("📊 Dashboard Cô Hà")
    password = st.sidebar.text_input("Nhập mật khẩu giáo viên:", type="password")
    # Bảo mật mật khẩu dashboard
    correct_pass = st.secrets["TEACHER_PASSWORD"] if "TEACHER_PASSWORD" in st.secrets else "CoHa9.0"
    if password == correct_pass:
        st.success("Chào mừng Cô Hà quay trở lại! ❤️")
        try:
            data_rows = sheet.get_all_records()
            if data_rows:
                df = pd.DataFrame(data_rows)
                col_name = 'Student Name' 
                col1, col2, col3 = st.columns(3)
                col1.metric("Tổng bài chấm", len(df))
                col2.metric("Số học sinh", df[col_name].nunique())
                col3.metric("Bài nộp gần nhất", df[col_name].iloc[-1])
                st.bar_chart(df[col_name].value_counts())
                st.dataframe(df, use_container_width=True)
            else:
                st.info("Chưa có dữ liệu học sinh nộp bài Hà ơi!")
        except Exception as e:
            st.error(f"Lỗi: {e}")
    elif password != "":
        st.error("Mật khẩu chưa đúng rồi Hà ơi!")
