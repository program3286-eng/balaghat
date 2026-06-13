"""نظام إدارة البلاغات"""
import streamlit as st
from utils.database import init_db

st.set_page_config(page_title="نظام إدارة البلاغات", page_icon="🔧", layout="wide", initial_sidebar_state="collapsed")
st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;500;700&display=swap');
html,body,[class*="css"],.stApp{font-family:'Tajawal',sans-serif!important;direction:rtl}
section[data-testid="stSidebar"]{direction:rtl;background:linear-gradient(180deg,#1a3c6e,#0d2447)}
section[data-testid="stSidebar"] *{color:#fff!important}
section[data-testid="stSidebar"] .stButton button{width:100%;background:rgba(255,255,255,0.1);border:1px solid rgba(255,255,255,0.2);color:#fff!important;border-radius:8px;margin:2px 0;text-align:right;padding:8px 16px}
.stButton button{border-radius:8px;font-family:'Tajawal',sans-serif}
h1,h2,h3,h4{font-family:'Tajawal',sans-serif!important;color:#1a3c6e}
#MainMenu,footer,header{visibility:hidden}
section[data-testid="stSidebarNav"],[data-testid="stSidebarNavItems"],[data-testid="collapsedControl"]{display:none!important}
.user-card{background:rgba(255,255,255,0.15);border-radius:12px;padding:12px;margin-bottom:16px;text-align:center}
</style>""", unsafe_allow_html=True)

init_db()

# ── مسح الـ session تماماً - لا نثق في أي بيانات محفوظة ──
if "authenticated" not in st.session_state:
    st.session_state.clear()
    st.session_state["authenticated"] = False
    st.session_state["user"] = None
    st.session_state["page"] = "login"
    st.session_state["edit_case_id"] = None

if not st.session_state.get("authenticated", False):
    st.session_state["user"] = None
    st.session_state["page"] = "login"
    st.markdown("<style>section[data-testid='stSidebar'],[data-testid='collapsedControl']{display:none!important}</style>", unsafe_allow_html=True)
    from pages.login import show as show_login
    show_login()
    st.stop()

user = st.session_state["user"]
role = user["role"]

if user.get("must_change_password"):
    from pages.change_password import show as show_change_pwd
    show_change_pwd(forced=True)
    st.stop()

with st.sidebar:
    role_labels = {"Admin":"🔴 مدير النظام","Manager":"🟠 مدير","User":"🔵 موظف","Viewer":"⚪ مشاهد"}
    st.markdown(f"""<div class="user-card"><div style="font-size:2rem">👤</div><div style="font-weight:bold;font-size:1.1rem">{user['employee_name']}</div><div style="font-size:0.85rem;opacity:0.8">@{user['username']}</div><div style="font-size:0.8rem;margin-top:4px">{role_labels.get(role,'')}</div></div>""", unsafe_allow_html=True)
    st.markdown("---")
    if role in ("Admin","Manager","User"):
        if st.button("➕ إضافة بلاغ جديد",key="nav_add"): st.session_state["page"]="add_case"; st.session_state["edit_case_id"]=None; st.rerun()
    if st.button("🔍 البحث وعرض البلاغات",key="nav_search"): st.session_state["page"]="search"; st.session_state["edit_case_id"]=None; st.rerun()
    if role in ("Admin","Manager","User"):
        if st.button("📤 استيراد من Excel",key="nav_import"): st.session_state["page"]="import"; st.rerun()
    if role in ("Admin","Manager"):
        st.markdown("---")
        if st.button("👥 إدارة المستخدمين",key="nav_users"): st.session_state["page"]="manage_users"; st.rerun()
        if st.button("📚 إدارة المراجع RESORS",key="nav_resources"): st.session_state["page"]="manage_resources"; st.rerun()
        if st.button("📜 سجل الحركات",key="nav_audit"): st.session_state["page"]="audit_log"; st.rerun()
    st.markdown("---")
    if st.button("🔐 تغيير كلمة المرور",key="nav_pwd"): st.session_state["page"]="change_password"; st.rerun()
    if st.button("🚪 تسجيل الخروج",key="nav_logout"):
        from utils.audit import log_action
        log_action(None,"تسجيل خروج",user["username"])
        st.session_state.clear()
        st.rerun()

page = st.session_state.get("page","add_case")
edit_id = st.session_state.get("edit_case_id")

if page in ("manage_users","manage_resources","audit_log") and role not in ("Admin","Manager"):
    st.error("⛔ ليس لديك صلاحية"); st.stop()
if page in ("add_case","edit_case"):
    if role=="Viewer": st.error("⛔ ليس لديك صلاحية"); st.stop()
    from pages.add_case import show as show_add; show_add(edit_id=edit_id)
elif page=="search":
    from pages.search_cases import show as show_search; show_search()
elif page=="manage_users":
    from pages.manage_users import show as show_users; show_users()
elif page=="manage_resources":
    from pages.manage_resources import show as show_resources; show_resources()
elif page=="audit_log":
    from pages.audit_log import show as show_audit; show_audit()
elif page=="import":
    from pages.import_excel import show as show_import; show_import()
elif page=="change_password":
    from pages.change_password import show as show_pwd; show_pwd()
else:
    if role in ("Admin","Manager","User"):
        from pages.add_case import show as show_add; show_add()
    else:
        from pages.search_cases import show as show_search; show_search()
