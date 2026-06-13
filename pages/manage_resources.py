"""
صفحة إدارة المراجع RESORS
"""
import streamlit as st
from datetime import datetime
from utils.auth import require_role, current_username
from utils.database import get_connection
from utils.calculations import get_all_resources
from utils.audit import log_action


def show():
    require_role(["Admin", "Manager"])

    st.subheader("📚 إدارة المراجع (RESORS)")
    st.caption("هذا الجدول يُحدد الرسوم والمركز والمصنعية لكل خدمة في كل محافظة")

    tab1, tab2 = st.tabs(["📋 عرض وتعديل المراجع", "➕ إضافة خدمة جديدة"])

    with tab1:
        _show_resources()

    with tab2:
        _add_resource()


def _show_resources():
    resources = get_all_resources()

    if not resources:
        st.info("لا توجد مراجع مضافة")
        return

    # تجميع حسب المحافظة
    by_gov = {}
    for r in resources:
        gov = r.get("governorate", "غير محدد")
        by_gov.setdefault(gov, []).append(r)

    for gov, rows in by_gov.items():
        st.markdown(f"### 🗺️ {gov}")
        for r in rows:
            with st.expander(f"🔧 {r['service_description']}"):
                with st.form(f"edit_res_{r['id']}"):
                    c1, c2, c3 = st.columns(3)
                    with c1:
                        technician = st.text_input("الفني", value=r.get("technician", ""))
                        total_fees = st.number_input("الرسوم (G)", value=float(r.get("total_fees") or 0), min_value=0.0)
                    with c2:
                        service_desc = st.text_input("وصف الخدمة", value=r.get("service_description", ""))
                        company_amount = st.number_input("الشركة (H)", value=float(r.get("company_amount") or 0), min_value=0.0)
                    with c3:
                        governorate = st.text_input("المحافظة", value=r.get("governorate", ""))
                        labor_amount = st.number_input("المصنعية (I)", value=float(r.get("labor_amount") or 0), min_value=0.0)

                    # المعادلات التلقائية
                    center_amount = total_fees - company_amount           # F = G - H
                    center_after_labor = center_amount - labor_amount     # J = F - I

                    st.info(f"📊 المركز (F = G-H) = **{center_amount:.2f}** | صافي المركز (J = F-I) = **{center_after_labor:.2f}**")

                    c1, c2 = st.columns(2)
                    with c1:
                        saved = st.form_submit_button("💾 حفظ", use_container_width=True)
                    with c2:
                        deleted = st.form_submit_button("🗑️ حذف", use_container_width=True)

                    if saved:
                        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        old_vals = dict(r)
                        conn = get_connection()
                        conn.execute("""
                            UPDATE resources SET technician=?, service_description=?,
                            center_amount=?, total_fees=?, company_amount=?, labor_amount=?,
                            center_after_labor=?, governorate=? WHERE id=?
                        """, (technician, service_desc, center_amount, total_fees,
                              company_amount, labor_amount, center_after_labor,
                              governorate, r["id"]))
                        conn.commit()
                        conn.close()
                        log_action(None, "تعديل مراجع RESORS", current_username(),
                                   old_values=old_vals,
                                   new_values={"service": service_desc, "fees": total_fees})
                        st.success("✅ تم حفظ التعديلات")
                        st.rerun()

                    if deleted:
                        conn = get_connection()
                        conn.execute("DELETE FROM resources WHERE id=?", (r["id"],))
                        conn.commit()
                        conn.close()
                        log_action(None, "حذف مراجع RESORS", current_username(),
                                   old_values={"service": r["service_description"]})
                        st.success("✅ تم حذف الخدمة")
                        st.rerun()


def _add_resource():
    with st.form("add_resource_form"):
        st.markdown("#### إضافة خدمة جديدة")
        c1, c2, c3 = st.columns(3)
        with c1:
            technician = st.text_input("الفني *")
            total_fees = st.number_input("الرسوم (G) *", value=0.0, min_value=0.0)
        with c2:
            service_desc = st.text_input("وصف الخدمة *")
            company_amount = st.number_input("مبلغ الشركة (H)", value=0.0, min_value=0.0)
        with c3:
            governorate = st.selectbox("المحافظة *", ["الاقصر", "اسوان"])
            labor_amount = st.number_input("المصنعية (I)", value=0.0, min_value=0.0)

        # حساب تلقائي
        center_amount = total_fees - company_amount
        center_after_labor = center_amount - labor_amount
        st.info(f"📊 المركز (F) = **{center_amount:.2f}** | صافي المركز (J) = **{center_after_labor:.2f}**")

        submitted = st.form_submit_button("➕ إضافة", use_container_width=True)

    if submitted:
        if not service_desc.strip():
            st.error("⚠️ وصف الخدمة مطلوب")
            return
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM resources WHERE governorate=?", (governorate,))
        count = cur.fetchone()[0]
        conn.execute("""
            INSERT INTO resources (technician, service_description, center_amount, total_fees,
                                   company_amount, labor_amount, center_after_labor, governorate, sort_order)
            VALUES (?,?,?,?,?,?,?,?,?)
        """, (technician, service_desc.strip(), center_amount, total_fees,
              company_amount, labor_amount, center_after_labor, governorate, count + 1))
        conn.commit()
        conn.close()
        log_action(None, "إضافة مراجع RESORS", current_username(),
                   new_values={"service": service_desc, "governorate": governorate})
        st.success("✅ تمت الإضافة بنجاح")
        st.rerun()
