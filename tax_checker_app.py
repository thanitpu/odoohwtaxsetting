import streamlit as st
import pandas as pd

st.set_page_config(page_title="Tax Profile Checker", layout="centered")
st.title("📄 ตรวจสอบการตั้งค่า Tax Profile จาก Odoo")

uploaded_file = st.file_uploader("📤 กรุณาอัปโหลดไฟล์ Excel ที่ได้ export จาก Odoo", type=["xlsx"])

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file)

        def check_tax_profiles_from_df(df):
            feedback = []

            def is_seven_percent(name):
                return isinstance(name, str) and "7%" in name

            def is_price_included(value):
                return value == "Tax Included"

            input_vat_7 = df[(df["type_tax_use"] == "Purchases") & (df["name"].apply(is_seven_percent))]
            if not any(input_vat_7["price_include_override"].apply(is_price_included)):
                feedback.append("ขาด Input VAT 7% แบบ included")

            output_vat_7 = df[(df["type_tax_use"] == "Sales") & (df["name"].apply(is_seven_percent))]
            if not any(output_vat_7["price_include_override"].apply(is_price_included)):
                feedback.append("ขาด Output VAT 7% แบบ included")

            if not feedback:
                return "✅ สมบูรณ์"
            else:
                return "❌ งานไม่สมบูรณ์ เนื่องจาก " + ", ".join(feedback)

        result = check_tax_profiles_from_df(df)
        st.success("ผลการตรวจสอบ:")
        st.markdown(f"**{result}**")

    except Exception as e:
        st.error(f"เกิดข้อผิดพลาดในการอ่านไฟล์: {e}")