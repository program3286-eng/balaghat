"""
صفحة تسجيل الدخول
"""
import streamlit as st
from utils.database import get_connection
from utils.password_utils import hash_password, verify_password
from datetime import datetime


def show():
    st.markdown("""
    <style>
    body, .stApp { direction: rtl; font-family: 'Tajawal', Arial, sans-serif; }
    </style>
    <link href="https://fonts.googleapis.com/css2?family=Tajawal:wght@400;700&display=swap" rel="stylesheet">
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown('<div style="text-align:center;font-size:2rem;color:#1a3c6e;font-weight:bold">🔧 نظام إدارة البلاغات</div>', unsafe_allow_html=True)
        st.markdown('<div style="text-align:center;color:#888;margin-bottom:20px">تسجيل الدخول للنظام</div>', unsafe_allow_html=True)
        st.markdown("---")

        # ── تأكد إن Admin موجود وكلمة مروره صح ──
        _ensure_admin()

        with st.form("login_form"):
            username = st.text_input("اسم المستخدم", placeholder="أدخل اسم المستخدم")
            password = st.text_input("كلمة المرور", type="password", placeholder="أدخل كلمة المرور")
            submitted = st.form_submit_button("دخول ←", use_container_width=True)

        if submitted:
            if not username or not password:
                st.error("⚠️ يرجى إدخال اسم المستخدم وكلمة المرور")
                return
            from utils.auth import login
            user, error = login(username.strip(), password)
            if user:
                st.session_state["user"] = user
                st.session_state["authenticated"] = True
                st.session_state["page"] = _get_default_page(user["role"])
                st.rerun()
            else:
                st.error(f"❌ {error}")

        st.markdown("---")
        st.caption("للحصول على حساب، تواصل مع مدير النظام")


def _ensure_admin():
    """تأكد إن Admin موجود بكلمة مرور admin123"""
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, password_hash FROM users WHERE username='admin'")
        row = cur.fetchone()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if row is None:
            # أنشئ Admin جديد
            conn.execute("""
                INSERT INTO users (employee_name, username, password_hash, role, is_active, must_change_password, created_by, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, ("مدير النظام", "admin", hash_password("admin123"), "Admin", 1, 0, "system", now))
            conn.commit()
        else:
            # تحديث كلمة المرور دائماً لضمان صحتها
            if not verify_password("admin123", row[1]):
                conn.execute("UPDATE users SET password_hash=? WHERE username='admin'",
                             (hash_password("admin123"),))
                conn.commit()
        conn.close()
    except Exception:
        pass


def _get_default_page(role: str) -> str:
    if role in ("Admin", "Manager", "User"):
        return "add_case"
    else:
        return "search"
