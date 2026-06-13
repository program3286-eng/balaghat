"""
صفحة البحث وعرض البلاغات
"""
import streamlit as st
from utils.auth import require_login, current_role, current_username, is_admin_or_manager
from utils.database import get_connection
from utils.excel_io import get_all_cases, export_data_excel, export_send_excel, export_spare_parts_excel
from utils.calculations import get_governorates, get_technicians
from utils.audit import log_action


def show():
    require_login()
    role = current_role()

    st.subheader("🔍 البحث وعرض البلاغات")

    govs = get_governorates()
    techs = get_technicians()

    with st.expander("🔎 فلاتر البحث", expanded=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            f_order = st.text_input("رقم أمر الشغل")
            f_gov = st.selectbox("المحافظة", ["الكل"] + govs)
        with c2:
            f_name = st.text_input("اسم العميل")
            f_tech = st.selectbox("الفني", ["الكل"] + techs)
        with c3:
            f_phone = st.text_input("رقم التليفون")
            f_send = st.selectbox("موقف الارسال", ["الكل", "تم", "لم يُرسل"])

        c1, c2 = st.columns(2)
        with c1:
            search_btn = st.button("🔍 بحث", use_container_width=True)
        with c2:
            refresh_btn = st.button("🔄 تحديث البيانات", use_container_width=True)

    filters = {}
    if f_order:
        filters["work_order_no"] = f_order
    if f_name:
        filters["customer_name"] = f_name
    if f_phone:
        filters["phone"] = f_phone
    if f_tech != "الكل":
        filters["technician"] = f_tech
    if f_gov != "الكل":
        filters["governorate"] = f_gov
    if f_send != "الكل":
        filters["send_status"] = f_send

    cases = get_all_cases(filters if (search_btn or refresh_btn or filters) else {})

    st.markdown(f"**إجمالي النتائج: {len(cases)} بلاغ**")

    # أزرار التصدير
    if role in ("Admin", "Manager", "User"):
        ec1, ec2, ec3 = st.columns(3)
        with ec1:
            if st.button("📥 تصدير DATA", use_container_width=True):
                data = export_data_excel(cases)
                log_action(None, "تصدير", current_username(), details="تصدير DATA")
                st.download_button("⬇️ تنزيل DATA.xlsx", data, "DATA.xlsx",
                                   "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        with ec2:
            if st.button("📥 تصدير SEND", use_container_width=True):
                data = export_send_excel(cases)
                log_action(None, "تصدير", current_username(), details="تصدير SEND")
                st.download_button("⬇️ تنزيل SEND.xlsx", data, "SEND.xlsx",
                                   "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        with ec3:
            if st.button("📥 تصدير قطع الغيار", use_container_width=True):
                data = export_spare_parts_excel(cases)
                log_action(None, "تصدير", current_username(), details="تصدير SPER PRTIES")
                st.download_button("⬇️ تنزيل SPARE.xlsx", data, "SPER_PRTIES.xlsx",
                                   "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    if not cases:
        st.info("لا توجد بلاغات مطابقة للبحث")
        return

    # عرض الجدول
    for c in cases:
        with st.container():
            col1, col2, col3, col4, col5 = st.columns([2, 3, 2, 2, 2])
            with col1:
                st.markdown(f"**{c.get('work_order_no', '-')}**")
            with col2:
                st.markdown(f"👤 {c.get('customer_name', '-')} | 📞 {c.get('phone1', '-')}")
            with col3:
                st.markdown(f"🗺️ {c.get('governorate', '-')}")
            with col4:
                send = c.get('send_status', '')
                badge = "✅ تم" if send == "تم" else "⏳ معلق"
                st.markdown(badge)
            with col5:
                btn_col1, btn_col2 = st.columns(2)
                with btn_col1:
                    if role in ("Admin", "Manager", "User"):
                        if st.button("✏️", key=f"edit_{c['id']}", help="تعديل"):
                            st.session_state["edit_case_id"] = c["id"]
                            st.session_state["page"] = "add_case"
                            st.rerun()
                with btn_col2:
                    if role in ("Admin", "Manager"):
                        if st.button("🗑️", key=f"del_{c['id']}", help="حذف"):
                            st.session_state[f"confirm_del_{c['id']}"] = True

            # تأكيد الحذف
            if st.session_state.get(f"confirm_del_{c['id']}"):
                st.warning(f"⚠️ هل أنت متأكد من حذف البلاغ رقم {c.get('work_order_no')}؟")
                dc1, dc2 = st.columns(2)
                with dc1:
                    if st.button("✅ نعم، احذف", key=f"yes_del_{c['id']}"):
                        _delete_case(c["id"], c.get("work_order_no"))
                        del st.session_state[f"confirm_del_{c['id']}"]
                        st.rerun()
                with dc2:
                    if st.button("❌ إلغاء", key=f"no_del_{c['id']}"):
                        del st.session_state[f"confirm_del_{c['id']}"]
                        st.rerun()

            # عرض التفاصيل
            with st.expander(f"📄 تفاصيل البلاغ {c.get('work_order_no', '')}"):
                d1, d2, d3 = st.columns(3)
                with d1:
                    st.write(f"**المنتج:** {c.get('product_type', '-')}")
                    st.write(f"**الموديل:** {c.get('device_model', '-')}")
                    st.write(f"**السريال:** {c.get('serial', '-')}")
                    st.write(f"**PNC:** {c.get('pnc', '-')}")
                with d2:
                    st.write(f"**الرسوم:** {c.get('fees', '-')}")
                    st.write(f"**المركز:** {c.get('center_amount', '-')}")
                    st.write(f"**المصنعية:** {c.get('labor_amount', '-')}")
                    st.write(f"**الشركة:** {c.get('company', '-')}")
                with d3:
                    st.write(f"**الفني:** {c.get('technician', '-')}")
                    st.write(f"**تاريخ التنفيذ:** {c.get('execution_date', '-')}")
                    st.write(f"**أُضيف بواسطة:** {c.get('created_by', '-')}")
                    st.write(f"**آخر تعديل:** {c.get('updated_by', '-')} في {c.get('updated_at', '-')}")
        st.divider()


def _delete_case(case_id: int, work_order_no: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM data_cases WHERE id=?", (case_id,))
    row = cur.fetchone()
    old_vals = dict(row) if row else {}
    cur.execute("DELETE FROM data_cases WHERE id=?", (case_id,))
    conn.commit()
    conn.close()
    log_action(work_order_no, "حذف", current_username(), old_values=old_vals)
    st.success(f"✅ تم حذف البلاغ {work_order_no}")
