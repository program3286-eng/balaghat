"""
إعداد قاعدة البيانات
"""
import sqlite3
import os
from datetime import datetime

DB_PATH = os.environ.get("DB_PATH", "maintenance.db")
DB_TYPE = os.environ.get("DB_TYPE", "sqlite")

def get_connection():
    if DB_TYPE == "postgresql":
        import psycopg2
        return psycopg2.connect(
            host=os.environ.get("PG_HOST", "localhost"),
            port=os.environ.get("PG_PORT", "5432"),
            database=os.environ.get("PG_DB", "maintenance_db"),
            user=os.environ.get("PG_USER", "postgres"),
            password=os.environ.get("PG_PASSWORD", ""),
        )
    else:
        conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

def init_db():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_name TEXT NOT NULL,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('Admin','Manager','User','Viewer')),
            is_active INTEGER DEFAULT 1,
            must_change_password INTEGER DEFAULT 0,
            created_by TEXT,
            created_at TEXT,
            updated_by TEXT,
            updated_at TEXT,
            last_login_at TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS data_cases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            governorate TEXT, work_order_no TEXT UNIQUE, phone1 TEXT, phone2 TEXT,
            customer_name TEXT, address TEXT, product_type TEXT, customer_complaint TEXT,
            booking_date TEXT, device_model TEXT, device_color TEXT, screen_or_lamps TEXT,
            pnc TEXT, serial TEXT, technical_report TEXT, execution_date TEXT,
            collection_reason TEXT, fees REAL, travel_fees REAL, spare_parts_price REAL,
            shipping_fees REAL, discounts REAL, center_amount REAL, labor_amount REAL,
            technician TEXT, receipt_no TEXT, invoice_book_status TEXT, invoice_status TEXT,
            warranty_status TEXT, production_date TEXT, warranty_date TEXT, quantity TEXT,
            spare_part_code1 TEXT, spare_part_desc1 TEXT, spare_part_code2 TEXT, spare_part_desc2 TEXT,
            spare_part_code3 TEXT, spare_part_desc3 TEXT, spare_part_code4 TEXT, spare_part_desc4 TEXT,
            spare_part_code5 TEXT, spare_part_desc5 TEXT, invoice_closer TEXT, notes TEXT,
            followup_report TEXT, followup_by TEXT, company TEXT, spare_parts_after_discount REAL,
            shipping_fees2 REAL, net_center_inspections REAL, manufacturer_spare_parts REAL,
            send_status TEXT, created_by TEXT, created_at TEXT, updated_by TEXT, updated_at TEXT,
            last_modified_token TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS resources (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            technician TEXT, service_description TEXT UNIQUE, center_amount REAL,
            total_fees REAL, company_amount REAL, labor_amount REAL,
            center_after_labor REAL, governorate TEXT, sort_order INTEGER DEFAULT 0
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            work_order_no TEXT, action_type TEXT, username TEXT,
            old_values TEXT, new_values TEXT, action_at TEXT, details TEXT
        )
    """)

    conn.commit()

    cur.execute("DELETE FROM users WHERE username='admin'")
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cur.execute("""
        INSERT INTO users (employee_name, username, password_hash, role, is_active, must_change_password, created_by, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, ("مدير النظام", "admin", "admin123", "Admin", 1, 0, "system", now))
    conn.commit()

    cur.execute("SELECT COUNT(*) FROM resources")
    if cur.fetchone()[0] == 0:
        _insert_default_resources(cur)
        conn.commit()

    conn.close()

def _insert_default_resources(cur):
    luxor_services = [
        ("فني 1", "كشف وتصليح - الأقصر", 100, 150, 30, 20, 80, "الاقصر", 1),
        ("فني 2", "تغيير قطعة غيار - الأقصر", 200, 250, 50, 30, 170, "الاقصر", 2),
        ("فني 3", "صيانة دورية - الأقصر", 80, 120, 20, 15, 65, "الاقصر", 3),
        ("فني 4", "إصلاح شاشة - الأقصر", 300, 380, 70, 50, 250, "الاقصر", 4),
        ("فني 1", "تبديل بطارية - الأقصر", 120, 180, 40, 25, 95, "الاقصر", 5),
        ("فني 2", "إصلاح لوحة - الأقصر", 400, 500, 100, 60, 340, "الاقصر", 6),
        ("فني 3", "معاينة بدون تصليح - الأقصر", 50, 70, 10, 8, 42, "الاقصر", 7),
        ("فني 4", "ضمان - الأقصر", 0, 0, 0, 0, 0, "الاقصر", 8),
        ("فني 1", "تنظيف جهاز - الأقصر", 60, 90, 15, 10, 50, "الاقصر", 9),
        ("فني 2", "برمجة - الأقصر", 150, 200, 35, 25, 125, "الاقصر", 10),
    ]
    aswan_services = [
        ("فني 5", "كشف وتصليح - أسوان", 110, 160, 32, 22, 88, "اسوان", 11),
        ("فني 6", "تغيير قطعة غيار - أسوان", 210, 260, 52, 32, 178, "اسوان", 12),
        ("فني 5", "صيانة دورية - أسوان", 85, 125, 22, 16, 69, "اسوان", 13),
        ("فني 6", "إصلاح شاشة - أسوان", 310, 390, 72, 52, 258, "اسوان", 14),
        ("فني 5", "تبديل بطارية - أسوان", 125, 185, 42, 26, 99, "اسوان", 15),
        ("فني 6", "إصلاح لوحة - أسوان", 410, 510, 102, 62, 348, "اسوان", 16),
        ("فني 5", "معاينة بدون تصليح - أسوان", 55, 75, 12, 9, 46, "اسوان", 17),
        ("فني 6", "ضمان - أسوان", 0, 0, 0, 0, 0, "اسوان", 18),
        ("فني 5", "تنظيف جهاز - أسوان", 65, 95, 16, 11, 54, "اسوان", 19),
        ("فني 6", "برمجة - أسوان", 155, 205, 37, 26, 129, "اسوان", 20),
    ]
    for svc in luxor_services + aswan_services:
        cur.execute("""
            INSERT OR IGNORE INTO resources
            (technician, service_description, center_amount, total_fees, company_amount, labor_amount, center_after_labor, governorate, sort_order)
            VALUES (?,?,?,?,?,?,?,?,?)
        """, svc)
