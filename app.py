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

# ── مسح الـ session دائماً عند فتح التطبيق ──
st.session_state.clear()
st.session_state["user"] = None
st.session_state["page"] = "login"
st.session_state["edit_case_id"] = None

st.markdown("<style>section[data-testid='stSidebar'],[data-testid='collapsedControl']{display:none!important}</style>", unsafe_allow_html=True)
from pages.login import show as show_login
show_login()
