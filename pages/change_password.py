"""
صفحة تغيير كلمة المرور الخاصة بالمستخدم
"""
import streamlit as st
from datetime import datetime
from utils.auth import require_login, current_username
from utils.password_utils import verify_password, hash_password
from utils.database import get_connection
from utils.audit import log_action


def show(forced=False):
    require_login()

    if forced:
        st.warning("⚠️ يجب تغيير كلمة المرور قبل الاستمرار")
        st.subheader("🔐 تغيير كلمة المرور الإجباري")
    else:
        st.subheader("🔐 تغيير كلمة المرور")

    with st.form("change_pwd_form"):
        if not forced:
            old_pwd = st.text_input("كلمة المرور الحالية", type="password")
        new_pwd = st.text_input("كلمة المرور الجديدة", type="password")
        confirm_pwd = st.text_input("تأكيد كلمة المرور الجديدة", type="password")
        submitted = st.form_submit_button("💾 تغيير كلمة المرور", use_container_width=True)

    if submitted:
        errors = []
        if not new_pwd:
            errors.append("يرجى إدخال كلمة المرور الجديدة")
        if len(new_pwd) < 6:
            errors.append("كلمة المرور يجب أن تكون 6 أحرف على الأقل")
        if new_pwd != confirm_pwd:
            errors.append("كلمتا المرور غير متطابقتين")

        uname = current_username()

        if not forced:
            # التحقق من كلمة المرور القديمة
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("SELECT password_hash FROM users WHERE username=?", (uname,))
            row = cur.fetchone()
            conn.close()
            if row and not verify_password(old_pwd, row[0]):
                errors.append("كلمة المرور الحالية غير صحيحة")

        if errors:
            for e in errors:
                st.error(f"⚠️ {e}")
            return

        new_hash = hash_password(new_pwd)
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn = get_connection()
        conn.execute("""
            UPDATE users SET password_hash=?, must_change_password=0, updated_at=?
            WHERE username=?
        """, (new_hash, now, uname))
        conn.commit()
        conn.close()

        # تحديث session
        st.session_state["user"]["must_change_password"] = 0
        log_action(None, "تغيير كلمة مرور", uname, details="تغيير كلمة المرور بواسطة المستخدم نفسه")
        st.success("✅ تم تغيير كلمة المرور بنجاح")

        if forced:
            st.session_state["page"] = "add_case"
            st.rerun()
