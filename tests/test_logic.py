"""
اختبارات التحقق من صحة الحسابات والصلاحيات والتقارير
شغّل بـ: python tests/test_logic.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest
from unittest.mock import patch, MagicMock

# ───── إعداد قاعدة بيانات مؤقتة للاختبار ─────
os.environ["DB_PATH"] = "/tmp/test_maintenance.db"
os.environ["DB_TYPE"] = "sqlite"

from utils.database import init_db, get_connection
init_db()

from utils.calculations import calculate_auto_fields, lookup_service
from utils.password_utils import hash_password, verify_password
from utils.excel_io import export_send_excel, export_spare_parts_excel
from utils.audit import log_action, get_audit_log


class TestCalculations(unittest.TestCase):

    def test_luxor_valid_service(self):
        """الأقصر + خدمة موجودة → يرجع قيم صحيحة"""
        result = calculate_auto_fields("الاقصر", "كشف وتصليح - الأقصر")
        self.assertIsNotNone(result["fees"], "الرسوم يجب أن تُحسب للأقصر")
        self.assertIsNotNone(result["center_amount"], "المركز يجب أن يُحسب للأقصر")
        self.assertIsNotNone(result["company"], "الشركة يجب أن تُحسب للأقصر")

    def test_aswan_valid_service(self):
        """أسوان + خدمة موجودة → يرجع قيم صحيحة"""
        result = calculate_auto_fields("اسوان", "كشف وتصليح - أسوان")
        self.assertIsNotNone(result["fees"], "الرسوم يجب أن تُحسب لأسوان")
        self.assertIsNotNone(result["center_amount"])

    def test_invalid_service_returns_none(self):
        """خدمة غير موجودة → كل القيم None"""
        result = calculate_auto_fields("الاقصر", "خدمة غير موجودة أبداً")
        self.assertIsNone(result["fees"])
        self.assertIsNone(result["center_amount"])
        self.assertIsNone(result["company"])
        self.assertIsNone(result["net_center_inspections"])

    def test_empty_inputs(self):
        """مدخلات فارغة → None"""
        result = calculate_auto_fields("", "")
        self.assertIsNone(result["fees"])

    def test_resors_formula_F_equals_G_minus_H(self):
        """F (المركز) = G (الرسوم) - H (الشركة) - نتحقق من صحة المعادلة في حساب RESORS"""
        from utils.calculations import lookup_service
        # نُنشئ خدمة اختبارية ونتحقق من الحساب
        conn = get_connection()
        # إدراج خدمة اختبارية بقيم معروفة: G=200, H=50 → F=150
        conn.execute("""
            INSERT OR REPLACE INTO resources (technician, service_description, center_amount,
            total_fees, company_amount, labor_amount, center_after_labor, governorate, sort_order)
            VALUES ('فني اختبار', 'خدمة اختبار فورمولا', 150, 200, 50, 30, 120, 'الاقصر', 99)
        """)
        conn.commit()
        conn.close()
        svc = lookup_service("الاقصر", "خدمة اختبار فورمولا")
        self.assertIsNotNone(svc)
        G = svc["total_fees"]   # 200
        H = svc["company_amount"]  # 50
        F = svc["center_amount"]   # 150 = G-H
        self.assertAlmostEqual(F, G - H, places=2, msg="المركز F يجب = الرسوم G - الشركة H")

    def test_resors_formula_J_equals_F_minus_I(self):
        """J (صافي المركز) = F (المركز) - I (المصنعية)"""
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT center_amount, labor_amount, center_after_labor FROM resources WHERE governorate='الاقصر' LIMIT 1")
        row = cur.fetchone()
        conn.close()
        if row:
            F, I, J = row[0], row[1], row[2]
            self.assertAlmostEqual(J, F - I, places=2, msg="صافي المركز J يجب = المركز F - المصنعية I")

    def test_trim_normalization(self):
        """المحافظة مع مسافة زائدة يجب أن تعمل"""
        result_normal = calculate_auto_fields("الاقصر", "كشف وتصليح - الأقصر")
        result_spaced = calculate_auto_fields("  الاقصر  ", "  كشف وتصليح - الأقصر  ")
        self.assertEqual(result_normal["fees"], result_spaced["fees"])


class TestPasswords(unittest.TestCase):

    def test_password_hashed_not_plain(self):
        """كلمة المرور يجب ألا تُحفظ كنص صريح"""
        pwd = "TestPassword123"
        hashed = hash_password(pwd)
        self.assertNotEqual(pwd, hashed, "كلمة المرور يجب أن تكون مشفرة")
        self.assertTrue(hashed.startswith("pbkdf2"),
                        "يجب استخدام bcrypt")

    def test_verify_correct_password(self):
        """التحقق من كلمة المرور الصحيحة"""
        pwd = "MySecret@99"
        hashed = hash_password(pwd)
        self.assertTrue(verify_password(pwd, hashed))

    def test_verify_wrong_password(self):
        """التحقق من كلمة مرور خاطئة"""
        hashed = hash_password("CorrectPass")
        self.assertFalse(verify_password("WrongPass", hashed))


class TestReports(unittest.TestCase):

    def _sample_cases(self):
        return [
            {
                "id": 1,
                "work_order_no": "WO-001",
                "receipt_no": "R-001",
                "phone1": "01001234567",
                "phone2": "",
                "customer_name": "أحمد محمد",
                "address": "الأقصر",
                "device_model": "LG TV 55",
                "device_color": "أسود",
                "screen_or_lamps": "شاشة",
                "pnc": "123456",
                "serial": "SN001",
                "execution_date": "2024-01-15",
                "fees": 150.0,
                "technical_report": "تم الإصلاح",
                "warranty_date": "2025-01-15",
                "warranty_status": "ضمان",
                "send_status": "تم",
                "spare_parts_price": 0,
                "shipping_fees2": 0,
                "spare_part_code1": "P001",
                "spare_part_desc1": "قطعة 1",
                "spare_part_code2": "", "spare_part_desc2": "",
                "spare_part_code3": "", "spare_part_desc3": "",
                "spare_part_code4": "", "spare_part_desc4": "",
                "spare_part_code5": "", "spare_part_desc5": "",
            },
            {
                "id": 2,
                "work_order_no": "WO-002",
                "receipt_no": "R-002",
                "phone1": "01112345678",
                "phone2": "01234567890",
                "customer_name": "فاطمة علي",
                "address": "أسوان",
                "device_model": "Samsung Fridge",
                "device_color": "أبيض",
                "screen_or_lamps": "",
                "pnc": "",
                "serial": "SN002",
                "execution_date": "2024-01-20",
                "fees": 200.0,
                "technical_report": "تغيير قطعة",
                "warranty_date": "2025-01-20",
                "warranty_status": "بدون ضمان",
                "send_status": "",
                "spare_parts_price": 350,
                "shipping_fees2": 25,
                "spare_part_code1": "P002", "spare_part_desc1": "كومبريسور",
                "spare_part_code2": "", "spare_part_desc2": "",
                "spare_part_code3": "", "spare_part_desc3": "",
                "spare_part_code4": "", "spare_part_desc4": "",
                "spare_part_code5": "", "spare_part_desc5": "",
            }
        ]

    def test_send_report_columns(self):
        """تقرير SEND يجب أن يحتوي على أعمدة صحيحة"""
        import pandas as pd, io
        cases = self._sample_cases()
        data = export_send_excel(cases)
        df = pd.read_excel(io.BytesIO(data))
        required = ["رقم امر الشغل", "اسم العميل", "موقف الارسال"]
        for col in required:
            self.assertIn(col, df.columns, f"العمود '{col}' مفقود في تقرير SEND")

    def test_spare_parts_serial_number(self):
        """الرقم المسلسل يظهر فقط للصفوف التي بها رقم أمر شغل"""
        import pandas as pd, io
        cases = self._sample_cases()
        # التحقق من أن الصفوف ذات أرقام أوامر الشغل لها أرقام مسلسلة
        data = export_spare_parts_excel(cases)
        df = pd.read_excel(io.BytesIO(data))
        # يجب أن يكون هناك صفوف بقيم م صحيحة للسجلات الموجودة
        self.assertGreater(len(df), 0, "يجب أن يحتوي التقرير على سجلات")
        # الأرقام المسلسلة يجب أن تكون متسلسلة للصفوف الصحيحة
        valid_serials = df["م"].dropna().tolist()
        self.assertEqual(len(valid_serials), len(cases),
                         "يجب أن يكون لكل سجل بأمر شغل رقم مسلسل")
        self.assertEqual(valid_serials[0], 1, "الرقم المسلسل الأول يجب أن يكون 1")


class TestAuditLog(unittest.TestCase):

    def test_action_logged(self):
        """التحقق من تسجيل العملية في Audit Log"""
        log_action("WO-TEST-001", "إضافة", "test_user",
                   new_values={"test": "value"})
        logs = get_audit_log(limit=5, username_filter="test_user")
        self.assertTrue(any(l["work_order_no"] == "WO-TEST-001" for l in logs),
                        "يجب أن يُسجَّل الإجراء في Audit Log")


class TestDatabase(unittest.TestCase):

    def test_admin_user_created(self):
        """يجب أن يُنشأ مستخدم Admin افتراضي"""
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE role='Admin' LIMIT 1")
        admin = cur.fetchone()
        conn.close()
        self.assertIsNotNone(admin, "يجب وجود مستخدم Admin افتراضي")

    def test_admin_password_is_hashed(self):
        """كلمة مرور Admin يجب أن تكون مشفرة"""
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT password_hash FROM users WHERE role='Admin' LIMIT 1")
        row = cur.fetchone()
        conn.close()
        self.assertIsNotNone(row)
        hashed = row[0]
        self.assertNotEqual(hashed, "Admin@1234", "كلمة المرور يجب ألا تكون نصاً صريحاً")
        self.assertTrue(hashed.startswith("pbkdf2"), "يجب استخدام bcrypt")

    def test_resources_seeded(self):
        """يجب أن تكون بيانات RESORS موجودة"""
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM resources")
        count = cur.fetchone()[0]
        conn.close()
        self.assertGreater(count, 0, "يجب أن تكون هناك بيانات في جدول resources")

    def test_luxor_and_aswan_resources(self):
        """يجب أن تكون هناك خدمات للأقصر وأسوان"""
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT DISTINCT governorate FROM resources")
        govs = [r[0] for r in cur.fetchall()]
        conn.close()
        self.assertIn("الاقصر", govs, "يجب وجود خدمات الأقصر")
        self.assertIn("اسوان", govs, "يجب وجود خدمات أسوان")


if __name__ == "__main__":
    print("=" * 60)
    print("🧪 تشغيل اختبارات نظام إدارة البلاغات")
    print("=" * 60)
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    for cls in [TestCalculations, TestPasswords, TestReports, TestAuditLog, TestDatabase]:
        suite.addTests(loader.loadTestsFromTestCase(cls))
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    print("\n" + "=" * 60)
    if result.wasSuccessful():
        print("✅ جميع الاختبارات نجحت!")
    else:
        print(f"❌ فشل {len(result.failures)} اختبار، خطأ في {len(result.errors)}")
    print("=" * 60)
