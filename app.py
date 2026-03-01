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
    st.error(f"Lỗi kết nối Sheets: {e}")

# --- 2. CẤU HÌNH AI GEMINI (An toàn) ---
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
    client_ai = genai.Client(api_key=API_KEY)
except Exception as e:
    st.error(f"Lỗi AI: {e}")

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
            with st.spinner("Cô Hà đang xem bài..."):
                try:
                    prompt = f"Bạn là cô Hà chấm bài Flyers cho {name}. Đề: {topic}. Bài: {writing}. Trả về JSON: {{\"score\":\"X/5 Shields\", \"annotated\":\"HTML\", \"feedback\":\"3 mục\"}}"
                    response = client_ai.models.generate_content(model='gemini-2.5-flash', contents=prompt)
                    match = re.search(r'\{.*\}', response.text, re.DOTALL)
                    if match:
                        data = json.loads(match.group().replace('\n', ' ').replace('\r', ''))
                        st.balloons()
                        st.markdown(f"### 🏆 Kết quả của {name}: {data.get('score')}")
                        st.markdown(f'<div style="background-color: #1E1E1E; color: #DCDCDC; padding: 25px; border-radius: 12px; line-height: 2; font-size: 18px;">{data.get("annotated")}</div>', unsafe_allow_html=True)
                        st.info(data.get('feedback'))
                        
                        now = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                        sheet.append_row([now, name, topic, writing, data.get('score'), data.get('feedback')])
                        st.toast("Đã lưu bài thành công! ✅")
                except Exception as e:
                    st.error(f"Lỗi: {e}")
        else:
            st.warning("Hà điền đủ Tên và Bài viết nha!")

# --- 5. CHẾ ĐỘ DASHBOARD CHO CÔ HÀ ---
else:
    st.title("📊 Dashboard Quản Lý Lớp Học")
    password = st.sidebar.text_input("Nhập mật khẩu giáo viên:", type="password")
    
    # Kiểm tra mật khẩu từ Secrets
    if password == st.secrets["TEACHER_PASSWORD"]:
        st.success("Chào mừng Cô Hà quay trở lại! ❤️")
        try:
            data_rows = sheet.get_all_records()
            if data_rows:
                df = pd.DataFrame(data_rows)
                # LƯU Ý: Tên cột phải khớp y hệt dòng 1 trong Google Sheets của Hà
                col_name = 'Student Name' 
                
                col1, col2, col3 = st.columns(3)
                col1.metric("Tổng số bài đã chấm", len(df))
                col2.metric("Số học sinh khác nhau", df[col_name].nunique())
                col3.metric("Bài nộp gần nhất", df[col_name].iloc[-1])
                
                st.markdown("---")
                st.subheader("📈 Top Học Sinh Chăm Chỉ")
                st.bar_chart(df[col_name].value_counts())
                
                st.subheader("📋 Sổ điểm chi tiết")
                st.dataframe(df, use_container_width=True)
            else:
                st.info("Chưa có dữ liệu học sinh nào nộp bài Hà ơi!")
        except Exception as e:
            st.error(f"Lỗi Dashboard: {e}")
    elif password != "":
        st.error("Mật khẩu chưa đúng rồi Hà ơi!")