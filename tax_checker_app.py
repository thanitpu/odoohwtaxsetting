import streamlit as st
import pandas as pd

st.set_page_config(page_title="Tax Profile Checker", layout="centered")
st.title("📄 ตรวจสอบการตั้งค่า Tax Profile จาก Odoo")

uploaded_file = st.file_uploader("📤 กรุณาอัปโหลดไฟล์ Excel ที่ได้ export จาก Odoo", type=["xlsx"])

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file)

        def check_tax_profiles_from_df(df):
            messages = []

            def is_seven_percent(name):
                return isinstance(name, str) and "7%" in name

            def is_price_included(value):
                return value == "Tax Included"

            # Input VAT 7% included (Purchases)
            input_vat_7 = df[(df["type_tax_use"] == "Purchases") & (df["name"].apply(is_seven_percent))]
            if any(input_vat_7["price_include_override"].apply(is_price_included)):
                messages.append("✅ พบ Input VAT 7% แบบ included")
            else:
                messages.append("❌ ขาด Input VAT 7% แบบ included")

            # Output VAT 7% included (Sales)
            output_vat_7 = df[(df["type_tax_use"] == "Sales") & (df["name"].apply(is_seven_percent))]
            if any(output_vat_7["price_include_override"].apply(is_price_included)):
                messages.append("✅ พบ Output VAT 7% แบบ included")
            else:
                messages.append("❌ ขาด Output VAT 7% แบบ included")

            return messages

        st.success("ผลการตรวจสอบ:")
        results = check_tax_profiles_from_df(df)
        for r in results:
            if "✅" in r:
                st.markdown(f"<span style='color:green'>{r}</span>", unsafe_allow_html=True)
            else:
                st.markdown(f"<span style='color:red'>{r}</span>", unsafe_allow_html=True)

    except Exception as e:
        st.error(f"เกิดข้อผิดพลาดในการอ่านไฟล์: {e}")