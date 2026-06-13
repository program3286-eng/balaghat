"""
صفحة إدارة المستخدمين - للمدير والأدمن فقط
"""
import streamlit as st
from datetime import datetime
from utils.auth import require_role, current_username, is_admin
from utils.password_utils import hash_password
from utils.database import get_connection
from utils.audit import log_action


def show():
    require_role(["Admin", "Manager"])
    is_adm = is_admin()
    current_user = current_username()

    st.subheader("👥 إدارة المستخدمين")

    tab1, tab2 = st.tabs(["📋 قائمة المستخدمين", "➕ إضافة مستخدم جديد"])

    with tab1:
        _show_users_list(is_adm, current_user)

    with tab2:
        _show_add_user(is_adm, current_user)


def _get_all_users():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users ORDER BY id")
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def _show_users_list(is_adm, current_user):
    users = _get_all_users()
    st.markdown(f"**إجمالي المستخدمين: {len(users)}**")

    for u in users:
        with st.container():
            c1, c2, c3, c4, c5 = st.columns([2, 2, 2, 1, 2])
            with c1:
                status_icon = "🟢" if u["is_active"] else "🔴"
                st.markdown(f"{status_icon} **{u['employee_name']}**")
                st.caption(f"@{u['username']}")
            with c2:
                role_badges = {
                    "Admin": "🔴 مدير نظام",
                    "Manager": "🟠 مدير",
                    "User": "🔵 موظف",
                    "Viewer": "⚪ مشاهد"
                }
                st.markdown(role_badges.get(u["role"], u["role"]))
            with c3:
                st.caption(f"آخر دخول: {u.get('last_login_at', 'لم يدخل بعد') or 'لم يدخل بعد'}")
                if u.get("must_change_password"):
                    st.caption("⚠️ يجب تغيير كلمة المرور")
            with c4:
                active_label = "إيقاف" if u["is_active"] else "تفعيل"
                # لا يمكن للمانجر تعديل الأدمن
                can_edit = is_adm or u["role"] not in ("Admin",)
                if can_edit and u["username"] != current_user:
                    if st.button(active_label, key=f"toggle_{u['id']}"):
                        _toggle_user(u["id"], u["is_active"], u["username"])
                        st.rerun()
            with c5:
                if can_edit and u["username"] != current_user:
                    col_a, col_b = st.columns(2)
                    with col_a:
                        if st.button("✏️ تعديل", key=f"edit_usr_{u['id']}"):
                            st.session_state["editing_user_id"] = u["id"]
                    with col_b:
                        if st.button("🔑 تغيير كلمة المرور", key=f"pwd_{u['id']}"):
                            st.session_state["reset_pwd_id"] = u["id"]

        # نموذج التعديل المضمّن
        if st.session_state.get("editing_user_id") == u["id"]:
            _show_edit_user_form(u, is_adm)

        # نموذج إعادة تعيين كلمة المرور
        if st.session_state.get("reset_pwd_id") == u["id"]:
            _show_reset_password_form(u)

        st.divider()


def _show_edit_user_form(u, is_adm):
    with st.form(f"edit_user_{u['id']}"):
        st.markdown(f"**تعديل بيانات: {u['employee_name']}**")
        new_name = st.text_input("اسم الموظف", value=u["employee_name"])

        # الأدمن يستطيع تغيير أي صلاحية، المانجر فقط User/Viewer
        if is_adm:
            role_options = ["Admin", "Manager", "User", "Viewer"]
        else:
            role_options = ["User", "Viewer"]

        role_idx = role_options.index(u["role"]) if u["role"] in role_options else 0
        new_role = st.selectbox("الصلاحية", role_options, index=role_idx)
        must_change = st.checkbox("إجبار تغيير كلمة المرور عند الدخول", value=bool(u.get("must_change_password")))

        c1, c2 = st.columns(2)
        with c1:
            save = st.form_submit_button("💾 حفظ التعديلات")
        with c2:
            cancel = st.form_submit_button("❌ إلغاء")

        if save:
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            conn = get_connection()
            conn.execute("""
                UPDATE users SET employee_name=?, role=?, must_change_password=?,
                updated_by=?, updated_at=? WHERE id=?
            """, (new_name, new_role, int(must_change), current_username(), now, u["id"]))
            conn.commit()
            conn.close()
            log_action(None, "تعديل مستخدم", current_username(),
                       old_values={"role": u["role"], "employee_name": u["employee_name"]},
                       new_values={"role": new_role, "employee_name": new_name})
            st.success("✅ تم تعديل بيانات المستخدم")
            del st.session_state["editing_user_id"]
            st.rerun()

        if cancel:
            del st.session_state["editing_user_id"]
            st.rerun()


def _show_reset_password_form(u):
    with st.form(f"reset_pwd_{u['id']}"):
        st.markdown(f"**إعادة تعيين كلمة مرور: {u['employee_name']}**")
        new_pwd = st.text_input("كلمة المرور الجديدة", type="password")
        confirm_pwd = st.text_input("تأكيد كلمة المرور", type="password")
        force_change = st.checkbox("إجبار المستخدم على تغييرها عند الدخول", value=True)

        c1, c2 = st.columns(2)
        with c1:
            save = st.form_submit_button("💾 تغيير كلمة المرور")
        with c2:
            cancel = st.form_submit_button("❌ إلغاء")

        if save:
            if not new_pwd:
                st.error("⚠️ يرجى إدخال كلمة المرور")
            elif new_pwd != confirm_pwd:
                st.error("⚠️ كلمتا المرور غير متطابقتين")
            elif len(new_pwd) < 6:
                st.error("⚠️ كلمة المرور يجب أن تكون 6 أحرف على الأقل")
            else:
                hashed = hash_password(new_pwd)
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                conn = get_connection()
                conn.execute("""
                    UPDATE users SET password_hash=?, must_change_password=?,
                    updated_by=?, updated_at=? WHERE id=?
                """, (hashed, int(force_change), current_username(), now, u["id"]))
                conn.commit()
                conn.close()
                log_action(None, "إعادة تعيين كلمة مرور", current_username(),
                           details=f"إعادة تعيين كلمة مرور المستخدم: {u['username']}")
                st.success("✅ تم تغيير كلمة المرور")
                del st.session_state["reset_pwd_id"]
                st.rerun()

        if cancel:
            del st.session_state["reset_pwd_id"]
            st.rerun()


def _show_add_user(is_adm, current_user_name):
    with st.form("add_user_form"):
        st.markdown("#### إنشاء حساب موظف جديد")

        emp_name = st.text_input("اسم الموظف الكامل *")
        username = st.text_input("اسم المستخدم (Username) *", help="يستخدم لتسجيل الدخول - لا يقبل مسافات")
        pwd = st.text_input("كلمة المرور الأولية *", type="password")
        confirm_pwd = st.text_input("تأكيد كلمة المرور *", type="password")

        if is_adm:
            role_options = ["Admin", "Manager", "User", "Viewer"]
        else:
            role_options = ["User", "Viewer"]

        role = st.selectbox("الصلاحية *", role_options,
                            index=role_options.index("User") if "User" in role_options else 0)
        must_change = st.checkbox("إجبار الموظف على تغيير كلمة المرور عند أول دخول", value=True)

        submitted = st.form_submit_button("➕ إنشاء الحساب", use_container_width=True)

    if submitted:
        errors = []
        if not emp_name.strip():
            errors.append("اسم الموظف مطلوب")
        if not username.strip():
            errors.append("اسم المستخدم مطلوب")
        if " " in username.strip():
            errors.append("اسم المستخدم لا يجب أن يحتوي على مسافات")
        if not pwd:
            errors.append("كلمة المرور مطلوبة")
        if pwd != confirm_pwd:
            errors.append("كلمتا المرور غير متطابقتين")
        if len(pwd) < 6:
            errors.append("كلمة المرور يجب أن تكون 6 أحرف على الأقل")

        if errors:
            for e in errors:
                st.error(f"⚠️ {e}")
            return

        # التحقق من عدم تكرار اسم المستخدم
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT id FROM users WHERE username=?", (username.strip(),))
        if cur.fetchone():
            conn.close()
            st.error(f"⚠️ اسم المستخدم '{username}' موجود مسبقاً")
            return

        hashed = hash_password(pwd)
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn.execute("""
            INSERT INTO users (employee_name, username, password_hash, role, is_active,
                               must_change_password, created_by, created_at)
            VALUES (?,?,?,?,?,?,?,?)
        """, (emp_name.strip(), username.strip(), hashed, role, 1, int(must_change), current_user_name, now))
        conn.commit()
        conn.close()

        log_action(None, "إنشاء مستخدم", current_user_name,
                   new_values={"username": username, "role": role, "employee_name": emp_name})
        st.success(f"✅ تم إنشاء حساب الموظف **{emp_name}** بنجاح")
        st.info(f"📋 بيانات الدخول:\n- اسم المستخدم: `{username}`\n- كلمة المرور: `{pwd}`")


def _toggle_user(user_id, current_active, username):
    new_status = 0 if current_active else 1
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    action = "تعطيل مستخدم" if new_status == 0 else "تفعيل مستخدم"
    conn = get_connection()
    conn.execute("UPDATE users SET is_active=?, updated_by=?, updated_at=? WHERE id=?",
                 (new_status, current_username(), now, user_id))
    conn.commit()
    conn.close()
    log_action(None, action, current_username(), details=f"المستخدم: {username}")
