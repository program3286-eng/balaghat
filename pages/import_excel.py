"""
صفحة استيراد ملف Excel
"""
import streamlit as st
from utils.auth import require_role, current_username
from utils.excel_io import import_from_excel


def show():
    require_role(["Admin", "Manager", "User"])

    st.subheader("📤 استيراد بيانات من Excel")

    st.info("""
    **تعليمات الاستيراد:**
    - يجب أن يحتوي الملف على نفس أسماء الأعمدة العربية لشيت DATA
    - الأعمدة المحسوبة (الرسوم/المركز/المصنعية/الشركة/صافي المركز) ستُحسب تلقائياً
    - رقم أمر الشغل مطلوب لكل صف
    """)

    uploaded = st.file_uploader("اختر ملف Excel", type=["xlsx", "xls"])

    if uploaded:
        on_duplicate = st.radio(
            "عند وجود رقم أمر شغل مكرر:",
            ["skip", "update"],
            format_func=lambda x: "تجاهل المكرر" if x == "skip" else "تحديث الموجود",
            horizontal=True
        )

        if st.button("📤 ابدأ الاستيراد", use_container_width=True):
            try:
                with st.spinner("جاري استيراد البيانات..."):
                    added, updated, skipped = import_from_excel(
                        uploaded.read(), current_username(), on_duplicate
                    )
                st.success(f"✅ تم الاستيراد:\n- **{added}** سجل جديد\n- **{updated}** سجل محدّث\n- **{skipped}** سجل متجاهل")
            except Exception as e:
                st.error(f"❌ خطأ في الاستيراد: {str(e)}")
