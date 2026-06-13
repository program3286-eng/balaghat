"""
الحسابات التلقائية - مطابقة لمعادلات Excel
"""
from utils.database import get_connection


def normalize(text: str) -> str:
    """تنظيف النص من المسافات الزائدة"""
    if not text:
        return ""
    return str(text).strip()


def get_resources_by_governorate(governorate: str):
    """جلب خدمات المحافظة من RESORS"""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT * FROM resources WHERE governorate=? ORDER BY sort_order",
        (normalize(governorate),)
    )
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def get_all_resources():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM resources ORDER BY governorate, sort_order")
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def get_technicians():
    """جلب قائمة الفنيين"""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT technician FROM resources WHERE technician IS NOT NULL AND technician != '' ORDER BY technician")
    rows = [r[0] for r in cur.fetchall()]
    conn.close()
    return rows


def get_governorates():
    """جلب قائمة المحافظات"""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT governorate FROM resources ORDER BY governorate")
    rows = [r[0] for r in cur.fetchall()]
    conn.close()
    return rows if rows else ["الاقصر", "اسوان"]


def get_services_by_governorate(governorate: str):
    """جلب قائمة الخدمات لمحافظة معينة"""
    resources = get_resources_by_governorate(governorate)
    return [r["service_description"] for r in resources]


def lookup_service(governorate: str, service_description: str):
    """
    VLOOKUP مطابق لمنطق Excel:
    - إذا المحافظة = الأقصر → ابحث في rows الأقصر
    - إذا المحافظة = أسوان → ابحث في rows أسوان
    يرجع dict بالحقول أو None
    """
    gov = normalize(governorate)
    svc = normalize(service_description)
    if not gov or not svc:
        return None
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT * FROM resources WHERE governorate=? AND TRIM(service_description)=? LIMIT 1",
        (gov, svc)
    )
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def calculate_auto_fields(governorate: str, collection_reason: str):
    """
    حساب الحقول التلقائية:
    R الرسوم = total_fees
    W المركز = center_amount
    X المصنعية = labor_amount
    AU الشركة = company_amount
    AX صافي المركز = center_after_labor
    """
    result = {
        "fees": None,
        "center_amount": None,
        "labor_amount": None,
        "company": None,
        "net_center_inspections": None,
    }
    if not governorate or not collection_reason:
        return result
    svc = lookup_service(governorate, collection_reason)
    if svc:
        result["fees"] = svc.get("total_fees")
        result["center_amount"] = svc.get("center_amount")
        result["labor_amount"] = svc.get("labor_amount")
        result["company"] = svc.get("company_amount")
        result["net_center_inspections"] = svc.get("center_after_labor")
    return result
