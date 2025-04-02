import streamlit as st
import pandas as pd
from datetime import datetime
from rapidfuzz import fuzz
import os
import hashlib

st.set_page_config(page_title="Tax Profile Checker", layout="centered")
st.title("📄 ตรวจสอบการตั้งค่า Tax Profile จาก Odoo")

LOG_PATH = "log/grading_log.csv"
STUDENT_LIST_PATH = "log/students_list_template_v2.xlsx"

@st.cache_data
def load_students():
    return pd.read_excel(STUDENT_LIST_PATH, dtype={"student_id": str})

def is_student_eligible(student_name, current_time):
    students = load_students()
    row = students[students['student_name'] == student_name]
    if row.empty:
        return False, "ชื่อนิสิตไม่อยู่ในรายชื่อ"
    row = row.iloc[0]
    if row['Status'] != 'Active':
        return False, f"นิสิตสถานะ {row['Status']} ไม่สามารถส่งงานได้"
    if not (row['StartDate'] <= current_time <= row['EndDate']):
        return False, "อยู่นอกช่วงเวลาที่กำหนด"
    return True, row['student_id']

if os.path.exists(LOG_PATH):
    grading_log = pd.read_csv(LOG_PATH)
else:
    grading_log = pd.DataFrame(columns=[
        "student_id", "student_name", "filename", "timestamp",
        "result", "similarity_with", "similarity_score", "df_string", "file_hash"
    ])

with st.form("submission_form"):
    student_name = st.text_input("📌 ชื่อ-นามสกุล").strip()
    uploaded_file = st.file_uploader("📤 กรุณาอัปโหลดไฟล์ Excel ที่ได้ export จาก Odoo", type=["xlsx"])
    submitted = st.form_submit_button("✅ Submit for Grading")

if submitted and uploaded_file:
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    is_ok, result_msg = is_student_eligible(student_name, current_time[:10])

    if not is_ok:
        st.error(result_msg)
    else:
        try:
            df = pd.read_excel(uploaded_file)

            def check_tax_profiles_from_df(df):
                messages = []
                def is_seven_percent(name):
                    return isinstance(name, str) and "7%" in name
                def is_price_included(value):
                    return value == "Tax Included"
                input_vat_7 = df[(df["type_tax_use"] == "Purchases") & (df["name"].apply(is_seven_percent))]
                if any(input_vat_7["price_include_override"].apply(is_price_included)):
                    messages.append("✅ พบ Input VAT 7% แบบ included")
                else:
                    messages.append("❌ ขาด Input VAT 7% แบบ included")
                output_vat_7 = df[(df["type_tax_use"] == "Sales") & (df["name"].apply(is_seven_percent))]
                if any(output_vat_7["price_include_override"].apply(is_price_included)):
                    messages.append("✅ พบ Output VAT 7% แบบ included")
                else:
                    messages.append("❌ ขาด Output VAT 7% แบบ included")
                return messages

            df_string = "\n".join([",".join(map(str, row)) for row in df.values])
            file_bytes = uploaded_file.getvalue()
            file_hash = hashlib.sha256(file_bytes).hexdigest()

            if file_hash in grading_log['file_hash'].values:
                st.warning("🚨 พบว่าไฟล์นี้ถูกส่งมาก่อนแล้วจากนิสิตคนอื่น")

            similarity_with = ""
            similarity_score = 0
            if not grading_log.empty:
                for _, row in grading_log.iterrows():
                    old_text = str(row['df_string'])
                    score = fuzz.ratio(df_string, old_text)
                    if score > similarity_score:
                        similarity_score = score
                        similarity_with = row['filename']

            results = check_tax_profiles_from_df(df)
            result_text = "\n".join(results)

            st.success("ผลการตรวจสอบ:")
            for line in results:
                color = 'green' if "✅" in line else 'red'
                st.markdown(f"<span style='color:{color}'>{line}</span>", unsafe_allow_html=True)

            if similarity_score >= 90:
                st.warning(f"⚠️ ไฟล์ของคุณคล้ายกับ {similarity_with} ({similarity_score:.2f}%)")

            students_df = load_students()
            student_id = students_df[students_df["student_name"] == student_name]["student_id"].values[0]
            grading_log.loc[len(grading_log)] = [
                student_id, student_name, uploaded_file.name, current_time,
                result_text, similarity_with, similarity_score, df_string, file_hash
            ]
            grading_log.to_csv(LOG_PATH, index=False)

        except Exception as e:
            st.error(f"เกิดข้อผิดพลาดในการประมวลผลไฟล์: {e}")
