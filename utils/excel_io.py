"""
استيراد وتصدير ملفات Excel
"""
import io
import pandas as pd
from datetime import datetime
from utils.database import get_connection
from utils.calculations import calculate_auto_fields, normalize
from utils.audit import log_action

COLUMN_MAP = {
    "governorate": "المحافظه",
    "work_order_no": "رقم امر الشغل",
    "phone1": "التليفون1",
    "phone2": "التليفون 2",
    "customer_name": "اسم العميل",
    "address": "العنوان مفصل",
    "product_type": "نوع المنتج",
    "customer_complaint": "شكوي العميل",
    "booking_date": "تاريخ الحجز",
    "device_model": "موديل الجهاز",
    "device_color": "لون الجهاز",
    "screen_or_lamps": "شاشه ام لمبات",
    "pnc": "PNC",
    "serial": "السريال",
    "technical_report": "التقرير الفني",
    "execution_date": "تاريخ التنفيذ",
    "collection_reason": "سبب لتحصيل",
    "fees": "الرسوم",
    "travel_fees": "رسوم بدل الانتقال",
    "spare_parts_price": "ثمن قطعه الغيار",
    "shipping_fees": "رسوم الشحن",
    "discounts": "الخصومات",
    "center_amount": "المركز",
    "labor_amount": "المصنعيه",
    "technician": "الفني المستلم",
    "receipt_no": "رقم ايصال التحصيل",
    "invoice_book_status": "موقف تدوين الفاتورة بالدفتر",
    "invoice_status": "موقف الفاتورة",
    "warranty_status": "موقف الضمان",
    "production_date": "تاريخ الانتاج",
    "warranty_date": "تاريخ الضمان",
    "quantity": "الكمية",
    "spare_part_code1": "كود قطعة الغيار",
    "spare_part_desc1": "وصف قطعة الغيار",
    "spare_part_code2": "كود قطعة الغيار1",
    "spare_part_desc2": "وصف قطع الغيار1",
    "spare_part_code3": "كود قطعة الغيار2",
    "spare_part_desc3": "وصف قطع الغيار2",
    "spare_part_code4": "كود قطعة الغيار3",
    "spare_part_desc4": "وصف قطع الغيار3",
    "spare_part_code5": "كود قطعة الغيار4",
    "spare_part_desc5": "وصف قطع الغيار4",
    "invoice_closer": "القائم بالقفيل",
    "notes": "ملاحظات",
    "followup_report": "تقرير المتابعه التليفونيه",
    "followup_by": "القائم بالمتابعه التليفونيه",
    "company": "الشركه",
    "spare_parts_after_discount": "قطع الغيار بعد الخصم",
    "shipping_fees2": "رسوم الشحن2",
    "net_center_inspections": "صافي المركز في المعاينات",
    "manufacturer_spare_parts": "مصنعين قطع الغيار",
    "send_status": "موقف الارسال",
    "created_by": "أضيف بواسطة",
    "created_at": "تاريخ الإضافة",
    "updated_by": "عدّل بواسطة",
    "updated_at": "تاريخ آخر تعديل",
}

REVERSE_MAP = {v: k for k, v in COLUMN_MAP.items()}


def get_all_cases(filters=None):
    conn = get_connection()
    cur = conn.cursor()
    query = "SELECT * FROM data_cases WHERE 1=1"
    params = []
    if filters:
        if filters.get("work_order_no"):
            query += " AND work_order_no LIKE ?"
            params.append(f"%{filters['work_order_no']}%")
        if filters.get("customer_name"):
            query += " AND customer_name LIKE ?"
            params.append(f"%{filters['customer_name']}%")
        if filters.get("phone"):
            query += " AND (phone1 LIKE ? OR phone2 LIKE ?)"
            params.append(f"%{filters['phone']}%")
            params.append(f"%{filters['phone']}%")
        if filters.get("technician"):
            query += " AND technician=?"
            params.append(filters["technician"])
        if filters.get("governorate"):
            query += " AND governorate=?"
            params.append(filters["governorate"])
        if filters.get("send_status"):
            if filters["send_status"] == "تم":
                query += " AND send_status='تم'"
            elif filters["send_status"] == "لم يُرسل":
                query += " AND (send_status IS NULL OR send_status='')"
    query += " ORDER BY id DESC"
    cur.execute(query, params)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def export_data_excel(cases: list) -> bytes:
    """تصدير DATA إلى Excel"""
    df = pd.DataFrame(cases)
    # إعادة تسمية الأعمدة بالعربية
    rename_cols = {k: v for k, v in COLUMN_MAP.items() if k in df.columns}
    df = df.rename(columns=rename_cols)
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="DATA", index=False)
    return buf.getvalue()


def export_send_excel(cases: list) -> bytes:
    """تصدير تقرير SEND"""
    send_cols = [
        ("work_order_no", "رقم امر الشغل"),
        ("receipt_no", "رقم ايصال التحصيل"),
        ("phone1", "التليفون1"),
        ("phone2", "التليفون 2"),
        ("customer_name", "اسم العميل"),
        ("address", "العنوان مفصل"),
        ("device_model", "موديل الجهاز"),
        ("device_color", "لون الجهاز"),
        ("screen_or_lamps", "شاشه ام لمبات"),
        ("pnc", "PNC"),
        ("serial", "السريال"),
        ("execution_date", "تاريخ التنفيذ"),
        ("fees", "الرسوم"),
        ("technical_report", "التقرير الفني"),
        ("warranty_date", "تاريخ الضمان"),
        ("warranty_status", "موقف الضمان"),
        ("send_status", "موقف الارسال"),
    ]
    rows = []
    for c in cases:
        row = {arabic: c.get(eng) for eng, arabic in send_cols}
        rows.append(row)
    df = pd.DataFrame(rows, columns=[a for _, a in send_cols])
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="SEND", index=False)
    return buf.getvalue()


def export_spare_parts_excel(cases: list) -> bytes:
    """تصدير تقرير SPER PRTIES"""
    sper_cols = [
        ("م", "م"),
        ("work_order_no", "رقم امر الشغل"),
        ("receipt_no", "رقم ايصال التحصيل"),
        ("shipping_fees2", "رسوم الشحن"),
        ("spare_parts_price", "ثمن قطعه الغيار"),
        ("customer_name", "اسم العميل"),
        ("warranty_date", "تاريخ الضمان"),
        ("warranty_status", "موقف الضمان"),
        ("device_model", "موديل الجهاز"),
        ("spare_part_code1", "كود قطعة الغيار"),
        ("spare_part_desc1", "وصف قطعة الغيار"),
        ("execution_date", "تاريخ التنفيذ"),
        ("spare_part_code2", "كود قطعة الغيار1"),
        ("spare_part_desc2", "وصف قطع الغيار1"),
        ("spare_part_code3", "كود قطعة الغيار2"),
        ("spare_part_desc3", "وصف قطع الغيار2"),
        ("spare_part_code4", "كود قطعة الغيار3"),
        ("spare_part_desc4", "وصف قطع الغيار3"),
        ("spare_part_code5", "كود قطعة الغيار4"),
        ("spare_part_desc5", "وصف قطع الغيار4"),
        ("send_status", "موقف الارسال"),
    ]
    rows = []
    serial_counter = 0
    for c in cases:
        won = c.get("work_order_no")
        if won and str(won).strip() not in ("", "None", "nan"):
            serial_counter += 1
            row = {"م": serial_counter}
        else:
            row = {"م": ""}
        for eng, arabic in sper_cols:
            if eng == "م":
                continue
            row[arabic] = c.get(eng)
        rows.append(row)
    col_names = [a for _, a in sper_cols]
    df = pd.DataFrame(rows, columns=col_names)
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="SPER PRTIES", index=False)
    return buf.getvalue()


def import_from_excel(file_bytes: bytes, username: str, on_duplicate: str = "skip"):
    """
    استيراد من Excel
    on_duplicate: skip / update / new
    """
    df = pd.read_excel(io.BytesIO(file_bytes))
    # تنظيف أسماء الأعمدة
    df.columns = [normalize(c) for c in df.columns]
    # تحويل أسماء الأعمدة العربية إلى الإنجليزية
    df = df.rename(columns=REVERSE_MAP)
    # تنظيف القيم
    df = df.applymap(lambda x: normalize(str(x)) if isinstance(x, str) else x)

    conn = get_connection()
    cur = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    added = 0
    updated = 0
    skipped = 0

    for _, row in df.iterrows():
        won = normalize(str(row.get("work_order_no", "")))
        if not won or won == "nan":
            continue

        # حساب الحقول التلقائية
        gov = normalize(str(row.get("governorate", "")))
        svc = normalize(str(row.get("collection_reason", "")))
        auto = calculate_auto_fields(gov, svc)
        for field, val in auto.items():
            if val is not None:
                row[field] = val

        # تحقق إذا الأمر موجود
        cur.execute("SELECT id FROM data_cases WHERE work_order_no=?", (won,))
        existing = cur.fetchone()

        if existing:
            if on_duplicate == "skip":
                skipped += 1
                continue
            elif on_duplicate == "update":
                update_fields = []
                update_vals = []
                for col in df.columns:
                    if col in ("id", "created_by", "created_at"):
                        continue
                    if col in row and str(row[col]) != "nan":
                        update_fields.append(f"{col}=?")
                        update_vals.append(str(row[col]) if str(row[col]) != "nan" else None)
                update_fields.extend(["updated_by=?", "updated_at=?"])
                update_vals.extend([username, now, won])
                q = f"UPDATE data_cases SET {', '.join(update_fields)} WHERE work_order_no=?"
                cur.execute(q, update_vals)
                updated += 1

        else:
            # إضافة جديد
            fields = ["work_order_no", "created_by", "created_at"]
            vals = [won, username, now]
            for col in df.columns:
                if col in ("id", "work_order_no", "created_by", "created_at"):
                    continue
                v = row.get(col)
                if v is not None and str(v) != "nan":
                    fields.append(col)
                    vals.append(str(v))
            placeholders = ",".join(["?"] * len(vals))
            q = f"INSERT OR IGNORE INTO data_cases ({','.join(fields)}) VALUES ({placeholders})"
            cur.execute(q, vals)
            added += 1

    conn.commit()
    conn.close()
    log_action(None, "استيراد", username, details=f"استيراد: {added} إضافة، {updated} تحديث، {skipped} تجاهل")
    return added, updated, skipped
