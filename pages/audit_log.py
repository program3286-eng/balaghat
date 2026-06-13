"""
صفحة سجل الحركات Audit Log
"""
import streamlit as st
import json
from utils.auth import require_role
from utils.audit import get_audit_log


def show():
    require_role(["Admin", "Manager"])

    st.subheader("📜 سجل الحركات (Audit Log)")

    c1, c2, c3 = st.columns(3)
    with c1:
        user_filter = st.text_input("فلتر باسم المستخدم")
    with c2:
        action_options = ["الكل", "إضافة", "تعديل", "حذف", "تصدير", "تسجيل دخول",
                          "إنشاء مستخدم", "تعديل مستخدم", "إعادة تعيين كلمة مرور",
                          "تعطيل مستخدم", "تفعيل مستخدم", "إضافة مراجع RESORS",
                          "تعديل مراجع RESORS", "استيراد"]
        action_filter = st.selectbox("فلتر بنوع العملية", action_options)
    with c3:
        limit = st.number_input("عدد السجلات", value=100, min_value=10, max_value=1000, step=50)

    logs = get_audit_log(
        limit=limit,
        username_filter=user_filter if user_filter else None,
        action_filter=action_filter if action_filter != "الكل" else None
    )

    st.markdown(f"**إجمالي السجلات المعروضة: {len(logs)}**")

    if not logs:
        st.info("لا توجد سجلات")
        return

    for log in logs:
        action_icons = {
            "إضافة": "➕",
            "تعديل": "✏️",
            "حذف": "🗑️",
            "تصدير": "📥",
            "تسجيل دخول": "🔑",
            "إنشاء مستخدم": "👤",
            "استيراد": "📤",
        }
        icon = action_icons.get(log.get("action_type", ""), "📋")

        col1, col2, col3, col4 = st.columns([1, 2, 2, 3])
        with col1:
            st.markdown(f"{icon} **{log.get('action_type', '')}**")
        with col2:
            st.caption(f"👤 {log.get('username', '')}")
        with col3:
            st.caption(f"📋 {log.get('work_order_no', '-')}")
        with col4:
            st.caption(f"🕐 {log.get('action_at', '')}")

        if log.get("details"):
            st.caption(f"📝 {log['details']}")

        if log.get("old_values") or log.get("new_values"):
            with st.expander("عرض التفاصيل"):
                if log.get("old_values"):
                    try:
                        old = json.loads(log["old_values"])
                        st.write("**القيم القديمة:**")
                        st.json(old)
                    except Exception:
                        st.write(log["old_values"])
                if log.get("new_values"):
                    try:
                        new = json.loads(log["new_values"])
                        st.write("**القيم الجديدة:**")
                        st.json(new)
                    except Exception:
                        st.write(log["new_values"])

        st.divider()
