import streamlit as st
import google.generativeai as genai
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
import re
import pandas as pd
from datetime import datetime

# --- 1. KẾT NỐI GOOGLE SHEETS THÔNG MINH ---
try:
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    # Tự động chọn: Online dùng Secrets, Local dùng file key.json
    if "gcp_service_account" in st.secrets:
        creds_info = st.secrets["gcp_service_account"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_info, scope)
    else:
        creds = ServiceAccountCredentials.from_json_keyfile_name("key.json", scope)
        
    client_sheet = gspread.authorize(creds)
    sheet = client_sheet.open("HaWritingApp_Database").sheet1
except Exception as e:
    st.error(f"Lỗi kết nối Sheets: {e}")

# --- 2. CẤU HÌNH AI GEMINI ---
# Lấy API Key từ Secrets
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=API_KEY)
    # Dùng model ổn định nhất để tránh lỗi 404
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    st.error(f"Lỗi cấu hình AI: {e}")

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
            with st.spinner("Cô Hà đang chấm bài..."):
                try:
                    prompt = f"""
                    Bạn là cô Hà giáo viên tiếng Anh chấm Flyers cho {name}. Đề: {topic}. Bài: {writing}.
                    NHIỆM VỤ:
                    1. Annotated: Sửa TẤT CẢ lỗi (viết hoa, dấu câu, ngữ pháp). 
                       Dùng <strike style='color: #FF6B6B;'>sai</strike> <span style='color: #4ECDC4; font-weight: bold;'>đúng</span>.
                    2. Feedback: Viết ngắn gọn 3 mục (KHÔNG HTML, KHÔNG LIST):
                       - TỔNG KẾT LỖI & GIẢI PHÁP: 
                       - LEVEL UP: 
                       - KHÍCH LỆ:
                    TRẢ VỀ JSON: {{"score":"X/5 Shields", "annotated":"HTML...", "feedback":"Lời dặn 3 mục"}}
                    """
                    response = model.generate_content(prompt)
                    # Trích xuất JSON từ phản hồi của AI
                    match = re.search(r'\{.*\}', response.text, re.DOTALL)
                    if match:
                        data = json.loads(match.group().replace('\n', ' '))
                        st.balloons()
                        st.markdown(f"### 🏆 Kết quả của {name}: {data.get('score')}")
                        st.markdown(f'''<div style="background-color: #1E1E1E; padding: 25px; border-radius: 12px; line-height: 2;">{data.get('annotated')}</div>''', unsafe_allow_html=True)
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
    password = st.sidebar.text_input("Mật khẩu:", type="password")
    if password == st.secrets.get("TEACHER_PASSWORD", "CoHa9.0"):
        try:
            data = sheet.get_all_records()
            if data:
                df = pd.DataFrame(data)
                st.metric("Tổng bài chấm", len(df))
                st.dataframe(df, use_container_width=True)
            else:
                st.info("Chưa có bài nộp nào Hà ơi!")
        except Exception as e:
            st.error(f"Lỗi hiển thị Dashboard: {e}")
