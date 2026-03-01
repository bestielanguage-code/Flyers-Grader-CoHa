import streamlit as st
from google import genai
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
import re
import pandas as pd
from datetime import datetime
import os

# ==============================
# 1️⃣ GOOGLE SHEETS CONNECTION
# ==============================

def connect_sheets():
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]

    # Nếu chạy ONLINE → dùng st.secrets
    if "google_service_account" in st.secrets:
        creds_dict = dict(st.secrets["google_service_account"])
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)

    # Nếu chạy LOCAL → dùng key.json
    else:
        creds = ServiceAccountCredentials.from_json_keyfile_name("key.json", scope)

    client = gspread.authorize(creds)
    return client.open("HaWritingApp_Database").sheet1


try:
    sheet = connect_sheets()
except Exception as e:
    st.error(f"Lỗi kết nối Google Sheets: {e}")


# ==============================
# 2️⃣ GEMINI CONFIG
# ==============================

def get_gemini_client():
    if "GEMINI_API_KEY" in st.secrets:
        api_key = st.secrets["GEMINI_API_KEY"]
    else:
        api_key = os.getenv("GEMINI_API_KEY")

    return genai.Client(api_key=api_key)


client_ai = get_gemini_client()


# ==============================
# 3️⃣ STREAMLIT UI
# ==============================

st.set_page_config(page_title="Flyers Grader", page_icon="✍️", layout="wide")

st.sidebar.title("💎 Cổng Điều Hướng")
role = st.sidebar.selectbox("Bạn là ai?", ["Học sinh nộp bài", "Cô Hà quản lý"])


# ==============================
# 4️⃣ STUDENT MODE
# ==============================

if role == "Học sinh nộp bài":

    st.title("Flyers Writing Grader - Cô Hà ✍️")

    name = st.text_input("Tên của con:")
    topic = st.text_input("Đề bài:")
    writing = st.text_area("Bài viết:", height=250)

    if st.button("Gửi bài 🚀"):

        if name and writing:

            with st.spinner("Cô Hà đang chấm bài..."):

                try:

                    prompt = f"""
Bạn là giáo viên chấm Flyers.

BẮT BUỘC TRẢ VỀ JSON HỢP LỆ.
KHÔNG giải thích.
KHÔNG markdown.

FORMAT:

{{
  "score": "X/5 Shields",
  "annotated": "HTML sửa bài",
  "feedback": "3 mục text thuần"
}}

Đề: {topic}
Học sinh: {name}
Bài viết:
{writing}
"""

                    response = client_ai.models.generate_content(
                        model="gemini-2.0-flash",
                        contents=prompt
                    )

                    # Lấy JSON an toàn
                    text = response.text.strip()

                    match = re.search(r'\{.*\}', text, re.DOTALL)
                    if not match:
                        raise ValueError("AI không trả về JSON")

                    data = json.loads(match.group())

                    st.success(f"🏆 {data['score']}")
                    st.markdown(data["annotated"], unsafe_allow_html=True)
                    st.info(data["feedback"])

                    # Save to Sheets
                    now = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                    sheet.append_row([
                        now,
                        name,
                        topic,
                        writing,
                        data["score"],
                        data["feedback"]
                    ])

                    st.toast("Đã lưu bài thành công ✅")

                except Exception as e:
                    st.error(f"Lỗi AI hoặc Sheets: {e}")

        else:
            st.warning("Điền đủ tên và bài viết nha!")


# ==============================
# 5️⃣ DASHBOARD MODE
# ==============================

else:

    st.title("📊 Dashboard")

    password = st.sidebar.text_input("Nhập mật khẩu:", type="password")

    if password == "CoHa9.0":

        try:
            rows = sheet.get_all_records()

            if rows:
                df = pd.DataFrame(rows)
                st.dataframe(df, use_container_width=True)

                st.bar_chart(df.iloc[:,1].value_counts())
            else:
                st.info("Chưa có dữ liệu.")

        except Exception as e:
            st.error(f"Lỗi Dashboard: {e}")

    elif password != "":
        st.error("Sai mật khẩu!")
