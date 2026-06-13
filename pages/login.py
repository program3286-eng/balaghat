"""
صفحة تسجيل الدخول
"""
import streamlit as st
from utils.auth import login

def show():
    # CSS عربي RTL
    st.markdown("""
    <style>
    body, .stApp { direction: rtl; font-family: 'Tajawal', Arial, sans-serif; }
    .login-box { max-width: 420px; margin: 60px auto; padding: 40px; background: #fff; border-radius: 16px; box-shadow: 0 4px 24px #0002; }
    .login-title { text-align: center; font-size: 2rem; color: #1a3c6e; margin-bottom: 8px; }
    .login-sub { text-align: center; color: #888; margin-bottom: 24px; }
    </style>
    <link href="https://fonts.googleapis.com/css2?family=Tajawal:wght@400;700&display=swap" rel="stylesheet">
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown('<div class="login-title">🔧 نظام إدارة البلاغات</div>', unsafe_allow_html=True)
        st.markdown('<div class="login-sub">تسجيل الدخول للنظام</div>', unsafe_allow_html=True)
        st.markdown("---")

        with st.form("login_form"):
            username = st.text_input("اسم المستخدم", placeholder="أدخل اسم المستخدم")
            password = st.text_input("كلمة المرور", type="password", placeholder="أدخل كلمة المرور")
            submitted = st.form_submit_button("دخول ←", use_container_width=True)

        if submitted:
            if not username or not password:
                st.error("⚠️ يرجى إدخال اسم المستخدم وكلمة المرور")
                return
            user, error = login(username.strip(), password)
            if user:
                st.session_state["user"] = user
                st.session_state["page"] = _get_default_page(user["role"])
                st.rerun()
            else:
                st.error(f"❌ {error}")

        st.markdown("---")
        st.caption("للحصول على حساب، تواصل مع مدير النظام")


def _get_default_page(role: str) -> str:
    if role in ("Admin", "Manager"):
        return "add_case"
    elif role == "User":
        return "add_case"
    else:
        return "search"
