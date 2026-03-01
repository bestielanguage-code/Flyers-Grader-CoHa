import streamlit as st
import google.generativeai as genai
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
import re

# --- KẾT NỐI BẢO MẬT ---
try:
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    # Nếu chạy Online, lấy từ Secrets. Nếu chạy Local, lấy từ file key.json
    if "gcp_service_account" in st.secrets:
        creds = ServiceAccountCredentials.from_json_keyfile_dict(dict(st.secrets["gcp_service_account"]), scope)
    else:
        creds = ServiceAccountCredentials.from_json_keyfile_name("key.json", scope)
    
    client_sheet = gspread.authorize(creds)
    sheet = client_sheet.open("HaWritingApp_Database").sheet1
except Exception as e:
    st.error(f"Lỗi kết nối: {e}")

# Cấu hình AI (Sửa lỗi 404)
API_KEY = st.secrets["GEMINI_API_KEY"] if "GEMINI_API_KEY" in st.secrets else "KEY_TAM_LOCAL"
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash') # Model ổn định nhất hiện nay

# --- PHẦN GIAO DIỆN GIỮ NGUYÊN NHƯ CŨ CỦA HÀ ---
# ... (Phần code hiển thị của Hà dán tiếp vào đây)
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
                    # Prompt tối ưu để AI trả về đúng định dạng
                    prompt = f"""
                    Bạn là cô Hà giáo viên tiếng Anh chấm Flyers cho {name}. Đề: {topic}. Bài: {writing}.
                    
                    NHIỆM VỤ:
                    1. Annotated: Sửa TẤT CẢ lỗi chính tả, ngữ pháp, VIẾT HOA, DẤU CÂU.
                       Dùng <strike style='color: #FF6B6B;'>lỗi sai</strike> và <span style='color: #4ECDC4; font-weight: bold;'>đúng</span>.
                    
                    2. Feedback: Viết ngắn gọn 3 mục (KHÔNG HTML):
                       - TỔNG KẾT LỖI & GIẢI PHÁP: 
                       - LEVEL UP (A2 Flyers): 
                       - KHÍCH LỆ:

                    TRẢ VỀ DUY NHẤT JSON THEO MẪU:
                    {{
                        "score": "X/5 Shields",
                        "annotated": "HTML sửa bài",
                        "feedback": "Văn bản 3 mục"
                    }}
                    """
                    # Sửa lỗi model tại đây
                    response = client_ai.models.generate_content(model='gemini-1.5-flash', contents=prompt)
                    
                    # Trích xuất JSON từ phản hồi của AI
                    text_response = response.text
                    match = re.search(r'\{.*\}', text_response, re.DOTALL)
                    
                    if match:
                        data = json.loads(match.group())
                        st.balloons()
                        st.markdown(f"### 🏆 Kết quả của {name}: {data.get('score')}")
                        st.markdown(f'''<div style="background-color: #1E1E1E; color: #DCDCDC; padding: 25px; border-radius: 12px; line-height: 2; font-size: 18px;">{data.get('annotated')}</div>''', unsafe_allow_html=True)
                        st.info(data.get('feedback'))
                        
                        # Lưu vào Sheets
                        now = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                        sheet.append_row([now, name, topic, writing, data.get('score'), data.get('feedback')])
                        st.toast("Đã lưu bài thành công! ✅")
                    else:
                        st.error("AI trả kết quả không đúng định dạng. Hà thử lại nhé!")
                        
                except Exception as e:
                    st.error(f"Lỗi chấm bài: {e}")
        else:
            st.warning("Hà điền đủ Tên và Bài viết nha!")

# --- 5. CHẾ ĐỘ DASHBOARD CHO CÔ HÀ ---
else:
    st.title("📊 Dashboard Quản Lý Lớp Học")
    password = st.sidebar.text_input("Nhập mật khẩu giáo viên:", type="password")
    
    # Bảo mật mật khẩu Dashboard
    MASTER_PASS = st.secrets["TEACHER_PASSWORD"] if "TEACHER_PASSWORD" in st.secrets else "CoHa9.0"
    
    if password == MASTER_PASS:
        st.success("Chào mừng Cô Hà quay trở lại! ❤️")
        try:
            data_rows = sheet.get_all_records()
            if data_rows:
                df = pd.DataFrame(data_rows)
                # Các thông số thống kê
                col1, col2 = st.columns(2)
                col1.metric("Tổng số bài đã chấm", len(df))
                col2.metric("Số học sinh", df['Student Name'].nunique() if 'Student Name' in df.columns else 0)
                
                st.markdown("---")
                st.subheader("📋 Sổ điểm chi tiết")
                st.dataframe(df, use_container_width=True)
            else:
                st.info("Chưa có dữ liệu học sinh nào nộp bài Hà ơi!")
        except Exception as e:
            st.error(f"Lỗi hiển thị Dashboard: {e}")
    elif password != "":
        st.error("Mật khẩu chưa đúng rồi Hà ơi!")
