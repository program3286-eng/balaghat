"""
وظائف المصادقة والصلاحيات
"""
import streamlit as st
from datetime import datetime
from utils.database import get_connection
from utils.audit import log_action
from utils.password_utils import hash_password, verify_password

__all__ = ["hash_password", "verify_password", "login", "require_login",
           "require_role", "current_user", "current_username", "current_role",
           "is_admin_or_manager", "is_admin"]


def get_user_by_username(username: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE username=? AND is_active=1", (username,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def login(username: str, password: str):
    user = get_user_by_username(username)
    if not user:
        return None, "اسم المستخدم غير موجود أو الحساب معطل"
    if not verify_password(password, user["password_hash"]):
        return None, "كلمة المرور غير صحيحة"
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = get_connection()
    conn.execute("UPDATE users SET last_login_at=? WHERE id=?", (now, user["id"]))
    conn.commit()
    conn.close()
    log_action(None, "تسجيل دخول", username, details="تسجيل دخول ناجح")
    return user, None


def require_login():
    if "user" not in st.session_state or st.session_state["user"] is None:
        st.error("يجب تسجيل الدخول أولاً")
        st.stop()


def require_role(allowed_roles: list):
    require_login()
    user = st.session_state["user"]
    if user["role"] not in allowed_roles:
        st.error("⛔ ليس لديك صلاحية للوصول إلى هذه الصفحة")
        st.stop()


def current_user():
    return st.session_state.get("user", None)

def current_username():
    u = current_user()
    return u["username"] if u else "system"

def current_role():
    u = current_user()
    return u["role"] if u else None

def is_admin_or_manager():
    return current_role() in ["Admin", "Manager"]

def is_admin():
    return current_role() == "Admin"
