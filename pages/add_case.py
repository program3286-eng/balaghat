"""
صفحة إضافة / تعديل البلاغات
"""
import streamlit as st
from datetime import datetime
from utils.auth import require_login, current_username, current_role
from utils.database import get_connection
from utils.calculations import (
    calculate_auto_fields, get_services_by_governorate,
    get_governorates, get_technicians, normalize
)
from utils.audit import log_action
import json


def show(edit_id=None):
    require_login()
    role = current_role()
    if role == "Viewer":
        st.error("⛔ ليس لديك صلاحية للوصول إلى هذه الصفحة")
        return

    editing = edit_id is not None
    case_data = {}
    last_token = None

    if editing:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM data_cases WHERE id=?", (edit_id,))
        row = cur.fetchone()
        conn.close()
        if row:
            case_data = dict(row)
            last_token = case_data.get("last_modified_token")
        else:
            st.error("البلاغ غير موجود")
            return

    st.markdown("""
    <style>
    .field-label { font-weight: bold; color: #1a3c6e; }
    .calc-field { background: #f0f7ff; border-radius: 8px; padding: 8px 12px; }
    </style>
    """, unsafe_allow_html=True)

    title = "✏️ تعديل بلاغ" if editing else "➕ إضافة بلاغ جديد"
    st.subheader(title)

    govs = get_governorates()
    techs = get_technicians()

    # استخدام session_state لتتبع التغييرات في المحافظة وسبب التحصيل
    gov_key = f"gov_{edit_id or 'new'}"
    svc_key = f"svc_{edit_id or 'new'}"

    if gov_key not in st.session_state:
        st.session_state[gov_key] = case_data.get("governorate", govs[0] if govs else "")
    if svc_key not in st.session_state:
        st.session_state[svc_key] = case_data.get("collection_reason", "")

    # حساب تلقائي
    auto_vals = calculate_auto_fields(st.session_state[gov_key], st.session_state[svc_key])

    with st.form(f"case_form_{edit_id or 'new'}"):
        st.markdown("#### 📋 البيانات الأساسية")
        c1, c2, c3 = st.columns(3)
        with c1:
            gov_idx = govs.index(st.session_state[gov_key]) if st.session_state[gov_key] in govs else 0
            governorate = st.selectbox("المحافظه *", govs, index=gov_idx, key=f"gov_sel_{edit_id or 'new'}")
        with c2:
            work_order_no = st.text_input("رقم أمر الشغل *", value=case_data.get("work_order_no", ""))
        with c3:
            product_type = st.text_input("نوع المنتج", value=case_data.get("product_type", ""))

        c1, c2, c3 = st.columns(3)
        with c1:
            customer_name = st.text_input("اسم العميل", value=case_data.get("customer_name", ""))
        with c2:
            phone1 = st.text_input("التليفون 1", value=case_data.get("phone1", ""))
        with c3:
            phone2 = st.text_input("التليفون 2", value=case_data.get("phone2", ""))

        address = st.text_input("العنوان مفصل", value=case_data.get("address", ""))
        customer_complaint = st.text_area("شكوي العميل", value=case_data.get("customer_complaint", ""), height=80)

        st.markdown("#### 🔧 بيانات الجهاز")
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            device_model = st.text_input("موديل الجهاز", value=case_data.get("device_model", ""))
        with c2:
            device_color = st.text_input("لون الجهاز", value=case_data.get("device_color", ""))
        with c3:
            screen_or_lamps = st.text_input("شاشه ام لمبات", value=case_data.get("screen_or_lamps", ""))
        with c4:
            pnc = st.text_input("PNC", value=case_data.get("pnc", ""))

        c1, c2, c3 = st.columns(3)
        with c1:
            serial = st.text_input("السريال", value=case_data.get("serial", ""))
        with c2:
            booking_date = st.text_input("تاريخ الحجز", value=case_data.get("booking_date", ""))
        with c3:
            execution_date = st.text_input("تاريخ التنفيذ", value=case_data.get("execution_date", ""))

        technical_report = st.text_area("التقرير الفني", value=case_data.get("technical_report", ""), height=80)

        st.markdown("#### 💰 بيانات التحصيل")
        services = get_services_by_governorate(governorate)
        svc_idx = 0
        if case_data.get("collection_reason") in services:
            svc_idx = services.index(case_data["collection_reason"])
        collection_reason = st.selectbox("سبب التحصيل *", [""] + services, index=svc_idx + 1 if services else 0)

        # الحقول المحسوبة تلقائياً
        auto = calculate_auto_fields(governorate, collection_reason)

        st.markdown('<div class="calc-field">', unsafe_allow_html=True)
        c1, c2, c3, c4, c5 = st.columns(5)
        with c1:
            st.metric("الرسوم (تلقائي)", auto["fees"] or "-")
        with c2:
            st.metric("المركز (تلقائي)", auto["center_amount"] or "-")
        with c3:
            st.metric("المصنعية (تلقائي)", auto["labor_amount"] or "-")
        with c4:
            st.metric("الشركة (تلقائي)", auto["company"] or "-")
        with c5:
            st.metric("صافي المركز (تلقائي)", auto["net_center_inspections"] or "-")
        st.markdown('</div>', unsafe_allow_html=True)
        st.caption("🔄 هذه القيم تُحسب تلقائياً من جدول المراجع RESORS")

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            travel_fees = st.number_input("رسوم بدل الانتقال", value=float(case_data.get("travel_fees") or 0), min_value=0.0)
        with c2:
            spare_parts_price = st.number_input("ثمن قطعه الغيار", value=float(case_data.get("spare_parts_price") or 0), min_value=0.0)
        with c3:
            shipping_fees = st.number_input("رسوم الشحن", value=float(case_data.get("shipping_fees") or 0), min_value=0.0)
        with c4:
            discounts = st.number_input("الخصومات", value=float(case_data.get("discounts") or 0), min_value=0.0)

        c1, c2, c3 = st.columns(3)
        with c1:
            receipt_no = st.text_input("رقم ايصال التحصيل", value=case_data.get("receipt_no", ""))
        with c2:
            tech_options = [""] + techs
            tech_idx = tech_options.index(case_data.get("technician", "")) if case_data.get("technician", "") in tech_options else 0
            technician = st.selectbox("الفني المستلم", tech_options, index=tech_idx)
        with c3:
            send_status = st.selectbox("موقف الارسال", ["", "تم"],
                index=1 if case_data.get("send_status") == "تم" else 0)

        st.markdown("#### 📄 بيانات الفاتورة والضمان")
        c1, c2, c3 = st.columns(3)
        with c1:
            invoice_book_status = st.text_input("موقف تدوين الفاتورة بالدفتر", value=case_data.get("invoice_book_status", ""))
        with c2:
            invoice_status = st.text_input("موقف الفاتورة", value=case_data.get("invoice_status", ""))
        with c3:
            warranty_status = st.text_input("موقف الضمان", value=case_data.get("warranty_status", ""))

        c1, c2, c3 = st.columns(3)
        with c1:
            production_date = st.text_input("تاريخ الانتاج", value=case_data.get("production_date", ""))
        with c2:
            warranty_date = st.text_input("تاريخ الضمان", value=case_data.get("warranty_date", ""))
        with c3:
            quantity = st.text_input("الكمية", value=case_data.get("quantity", ""))

        st.markdown("#### 🔩 قطع الغيار")
        for i in range(1, 6):
            suffix = "" if i == 1 else str(i - 1)
            c1, c2 = st.columns(2)
            with c1:
                globals()[f"spare_part_code{i}"] = st.text_input(
                    f"كود قطعة الغيار{suffix}", value=case_data.get(f"spare_part_code{i}", ""), key=f"spcode{i}_{edit_id or 'new'}")
            with c2:
                globals()[f"spare_part_desc{i}"] = st.text_input(
                    f"وصف قطعة الغيار{suffix}", value=case_data.get(f"spare_part_desc{i}", ""), key=f"spdesc{i}_{edit_id or 'new'}")

        st.markdown("#### 📝 ملاحظات ومتابعة")
        c1, c2 = st.columns(2)
        with c1:
            invoice_closer = st.text_input("القائم بالقفيل", value=case_data.get("invoice_closer", ""))
            followup_by = st.text_input("القائم بالمتابعة التليفونية", value=case_data.get("followup_by", ""))
        with c2:
            notes = st.text_area("ملاحظات", value=case_data.get("notes", ""), height=80)
            followup_report = st.text_area("تقرير المتابعة التليفونية", value=case_data.get("followup_report", ""), height=80)

        c1, c2, c3 = st.columns(3)
        with c1:
            spare_parts_after_discount = st.number_input("قطع الغيار بعد الخصم", value=float(case_data.get("spare_parts_after_discount") or 0), min_value=0.0)
        with c2:
            shipping_fees2 = st.number_input("رسوم الشحن (قطع غيار)", value=float(case_data.get("shipping_fees2") or 0), min_value=0.0)
        with c3:
            manufacturer_spare_parts = st.number_input("مصنعين قطع الغيار", value=float(case_data.get("manufacturer_spare_parts") or 0), min_value=0.0)

        st.markdown("---")
        submitted = st.form_submit_button("💾 حفظ البلاغ", use_container_width=True)

    if submitted:
        if not work_order_no.strip():
            st.error("⚠️ رقم أمر الشغل مطلوب")
            return

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        token = now
        conn = get_connection()
        cur = conn.cursor()

        # فحص تضارب التعديلات
        if editing:
            cur.execute("SELECT last_modified_token FROM data_cases WHERE id=?", (edit_id,))
            current_token_row = cur.fetchone()
            if current_token_row and current_token_row[0] != last_token:
                st.warning("⚠️ تنبيه: تم تعديل هذا البلاغ بواسطة مستخدم آخر منذ فتحه. هل تريد الاستمرار في الحفظ؟")
                # يمكن إضافة زر تأكيد هنا

        # التحقق من تكرار رقم أمر الشغل
        if not editing:
            cur.execute("SELECT id FROM data_cases WHERE work_order_no=?", (work_order_no.strip(),))
            if cur.fetchone():
                conn.close()
                st.error(f"⚠️ رقم أمر الشغل '{work_order_no}' موجود مسبقاً. استخدم التعديل.")
                return

        auto = calculate_auto_fields(governorate, collection_reason)

        fields_vals = {
            "governorate": governorate,
            "work_order_no": work_order_no.strip(),
            "phone1": phone1,
            "phone2": phone2,
            "customer_name": customer_name,
            "address": address,
            "product_type": product_type,
            "customer_complaint": customer_complaint,
            "booking_date": booking_date,
            "device_model": device_model,
            "device_color": device_color,
            "screen_or_lamps": screen_or_lamps,
            "pnc": pnc,
            "serial": serial,
            "technical_report": technical_report,
            "execution_date": execution_date,
            "collection_reason": collection_reason,
            "fees": auto["fees"],
            "travel_fees": travel_fees,
            "spare_parts_price": spare_parts_price,
            "shipping_fees": shipping_fees,
            "discounts": discounts,
            "center_amount": auto["center_amount"],
            "labor_amount": auto["labor_amount"],
            "technician": technician,
            "receipt_no": receipt_no,
            "invoice_book_status": invoice_book_status,
            "invoice_status": invoice_status,
            "warranty_status": warranty_status,
            "production_date": production_date,
            "warranty_date": warranty_date,
            "quantity": quantity,
            "spare_part_code1": globals().get("spare_part_code1", ""),
            "spare_part_desc1": globals().get("spare_part_desc1", ""),
            "spare_part_code2": globals().get("spare_part_code2", ""),
            "spare_part_desc2": globals().get("spare_part_desc2", ""),
            "spare_part_code3": globals().get("spare_part_code3", ""),
            "spare_part_desc3": globals().get("spare_part_desc3", ""),
            "spare_part_code4": globals().get("spare_part_code4", ""),
            "spare_part_desc4": globals().get("spare_part_desc4", ""),
            "spare_part_code5": globals().get("spare_part_code5", ""),
            "spare_part_desc5": globals().get("spare_part_desc5", ""),
            "invoice_closer": invoice_closer,
            "notes": notes,
            "followup_report": followup_report,
            "followup_by": followup_by,
            "company": auto["company"],
            "spare_parts_after_discount": spare_parts_after_discount,
            "shipping_fees2": shipping_fees2,
            "net_center_inspections": auto["net_center_inspections"],
            "manufacturer_spare_parts": manufacturer_spare_parts,
            "send_status": send_status,
            "last_modified_token": token,
        }

        try:
            if editing:
                old_vals = dict(case_data)
                fields_vals["updated_by"] = current_username()
                fields_vals["updated_at"] = now
                set_clause = ", ".join([f"{k}=?" for k in fields_vals])
                vals = list(fields_vals.values()) + [edit_id]
                cur.execute(f"UPDATE data_cases SET {set_clause} WHERE id=?", vals)
                conn.commit()
                log_action(work_order_no.strip(), "تعديل", current_username(),
                           old_values=old_vals, new_values=fields_vals)
                st.success("✅ تم تعديل البلاغ بنجاح")
            else:
                fields_vals["created_by"] = current_username()
                fields_vals["created_at"] = now
                keys = list(fields_vals.keys())
                vals = list(fields_vals.values())
                placeholders = ",".join(["?"] * len(vals))
                cur.execute(f"INSERT INTO data_cases ({','.join(keys)}) VALUES ({placeholders})", vals)
                conn.commit()
                log_action(work_order_no.strip(), "إضافة", current_username(),
                           new_values=fields_vals)
                st.success("✅ تم حفظ البلاغ بنجاح")
                # مسح النموذج
                for key in list(st.session_state.keys()):
                    if key.startswith(("gov_sel_", "spcode", "spdesc")):
                        del st.session_state[key]

            conn.close()
            st.rerun()
        except Exception as e:
            conn.close()
            st.error(f"❌ خطأ في الحفظ: {str(e)}")
