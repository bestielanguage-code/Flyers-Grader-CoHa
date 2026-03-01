import streamlit as st
from google import genai
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
import re
import pandas as pd
from datetime import datetime

# --- 1. KẾT NỐI GOOGLE SHEETS (Dùng Secrets) ---
try:
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_dict = st.secrets["gcp_service_account"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client_sheet = gspread.authorize(creds)
    # Tên file phải khớp 100% với Google Sheets của Hà
    sheet = client_sheet.open("HaWritingApp_Database").sheet1
except Exception as e:
    st.error(f"Lỗi kết nối Sheets: {e}")

# --- 2. CẤU HÌNH AI GEMINI (Dùng Secrets) ---
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
    client_ai = genai.Client(api_key=API_KEY)
except Exception as e:
    st.error(f"Lỗi cấu hình AI: {e}")

# --- 3. GIAO DIỆN & SIDEBAR ---
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
                    Bạn là cô Hà giáo viên tiếng Anh chấm bài Flyers cho {name}. Đề: {topic}. Bài: {writing}.
                    NHIỆM VỤ:
                    1. Annotated: Sửa TẤT CẢ lỗi chính tả, ngữ pháp, VIẾT HOA đầu câu/tên riêng, DẤU CÂU.
                       Dùng <strike style='color: #FF6B6B;'>lỗi sai</strike> và <span style='color: #4ECDC4; font-weight: bold;'>đúng</span>.
                    2. Feedback: Viết cực ngắn gọn 3 mục (KHÔNG HTML):
                       - TỔNG KẾT LỖI & GIẢI PHÁP: 
                       - LEVEL UP (A2 Flyers): 
                       - KHÍCH LỆ:
                    TRẢ VỀ DUY NHẤT 1 KHỐI JSON:
                    {{
                        "score": "X/5 Shields",
                        "annotated": "HTML sửa bài",
                        "feedback": "Lời dặn 3 mục"
                    }}
                    """
                    # Sử dụng model 1.5 Flash để ổn định tuyệt đối
                    response = client_ai.models.generate_content(model='gemini-1.5-flash', contents=prompt)
                    match = re.search(r'\{.*\}', response.text, re.DOTALL)
                    
                    if match:
                        data = json.loads(match.group().replace('\n', ' ').replace('\r', ''))
                        st.balloons()
                        st.markdown(f"### 🏆 Kết quả của {name}: {data.get('score')}")
                        
                        # Hiển thị bản sửa lỗi
                        st.subheader("📍 Bản sửa chi tiết:")
                        st.markdown(f'''<div style="background-color: #1E1E1E; color: #DCDCDC; padding: 25px; border-radius: 12px; line-height: 2; font-size: 18px;">
                            {data.get('annotated')}</div>''', unsafe_allow_html=True)
                        
                        st.markdown("---")
                        st.subheader("💬 Lời dặn từ Cô Hà:")
                        st.info(data.get('feedback'))
                        
                        # Lưu vào Sheets
                        now = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                        sheet.append_row([now, name, topic, writing, data.get('score'), data.get('feedback')])
                        st.toast("Đã lưu bài thành công! ✅")
                except Exception as e:
                    st.error(f"Lỗi AI: {e}")
        else:
            st.warning("Hà điền đủ Tên và Bài viết nha!")

# --- 5. CHẾ ĐỘ DASHBOARD ---
else:
    st.title("📊 Dashboard Cô Hà")
    password = st.sidebar.text_input("Nhập mật khẩu giáo viên:", type="password")
    
    if password == st.secrets["TEACHER_PASSWORD"]:
        st.success("Chào mừng Cô Hà! ❤️")
        try:
            data_rows = sheet.get_all_records()
            if data_rows:
                df = pd.DataFrame(data_rows)
                # Đảm bảo cột tên trong Sheets là "Student Name" hoặc sửa lại tại đây
                col_student = df.columns[1] 
                
                col1, col2 = st.columns(2)
                col1.metric("Tổng bài chấm", len(df))
                col2.metric("Số học sinh", df[col_student].nunique())
                
                st.subheader("📈 Top Học Sinh Chăm Chỉ")
                st.bar_chart(df[col_student].value_counts())
                
                st.subheader("📋 Sổ điểm chi tiết")
                st.dataframe(df, use_container_width=True)
            else:
                st.info("Chưa có bài nộp nào đâu Hà ơi!")
        except Exception as e:
            st.error(f"Lỗi Dashboard: {e}")
    elif password != "":
        st.error("Mật khẩu chưa đúng rồi Hà ơi!")
