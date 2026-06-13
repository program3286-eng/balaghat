#!/usr/bin/env python3
"""
سكريبت التشغيل الرئيسي
يشغّل Streamlit + FastAPI معاً
"""
import subprocess
import sys
import os
import time
import socket

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ─── إعدادات ───
STREAMLIT_PORT = int(os.environ.get("STREAMLIT_PORT", "8501"))
PWA_PORT       = int(os.environ.get("PWA_PORT", "80"))

# ─── تحديد الـ IP تلقائياً ───
def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def wait_for_port(port, timeout=30):
    """انتظر حتى يصبح المنفذ جاهزاً"""
    start = time.time()
    while time.time() - start < timeout:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=1):
                return True
        except Exception:
            time.sleep(0.5)
    return False


def main():
    ip = get_local_ip()
    pwa_port = PWA_PORT

    print("=" * 55)
    print("  🔧 نظام إدارة البلاغات — تشغيل PWA")
    print("=" * 55)

    # ─── 1. تشغيل Streamlit في الخلفية ───
    print(f"\n⏳ تشغيل النظام الداخلي (منفذ {STREAMLIT_PORT})...")
    streamlit_cmd = [
        sys.executable, "-m", "streamlit", "run",
        os.path.join(BASE_DIR, "app.py"),
        "--server.port", str(STREAMLIT_PORT),
        "--server.address", "127.0.0.1",
        "--server.headless", "true",
        "--server.enableCORS", "false",
        "--server.enableXsrfProtection", "false",
        "--browser.gatherUsageStats", "false",
    ]
    streamlit_proc = subprocess.Popen(
        streamlit_cmd,
        cwd=BASE_DIR,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    # انتظر Streamlit يكون جاهزاً
    if not wait_for_port(STREAMLIT_PORT, timeout=30):
        print("❌ فشل تشغيل Streamlit")
        streamlit_proc.terminate()
        sys.exit(1)
    print(f"  ✅ النظام الداخلي جاهز")

    # ─── 2. تشغيل FastAPI/PWA Server ───
    print(f"\n⏳ تشغيل سيرفر PWA (منفذ {pwa_port})...")
    try:
        import uvicorn
        from pwa_server import app as fastapi_app

        print("\n" + "=" * 55)
        print(f"  ✅ النظام جاهز!")
        print(f"\n  📱 رابط الدخول من الموبايل:")
        print(f"     http://{ip}:{pwa_port}")
        print(f"\n  🖥️  رابط الدخول من الكمبيوتر:")
        print(f"     http://localhost:{pwa_port}")
        print(f"\n  📲 عند فتح الرابط على أندرويد:")
        print(f"     سيظهر زر 'تثبيت التطبيق' تلقائياً")
        print("=" * 55)
        print("\n  ⏹  اضغط Ctrl+C للإيقاف\n")

        uvicorn.run(
            fastapi_app,
            host="0.0.0.0",
            port=pwa_port,
            log_level="warning",
        )
    except PermissionError:
        # المنفذ 80 يحتاج صلاحيات - جرّب 8080
        pwa_port = 8080
        print(f"\n⚠️  المنفذ 80 يحتاج صلاحيات - سيتم استخدام {pwa_port}")
        print("\n" + "=" * 55)
        print(f"  ✅ النظام جاهز!")
        print(f"\n  📱 رابط الدخول من الموبايل:")
        print(f"     http://{ip}:{pwa_port}")
        print(f"\n  🖥️  رابط الدخول من الكمبيوتر:")
        print(f"     http://localhost:{pwa_port}")
        print(f"\n  📲 عند فتح الرابط على أندرويد:")
        print(f"     سيظهر زر 'تثبيت التطبيق' تلقائياً")
        print("=" * 55)
        import uvicorn
        from pwa_server import app as fastapi_app
        uvicorn.run(fastapi_app, host="0.0.0.0", port=pwa_port, log_level="warning")
    except ImportError:
        print("❌ يرجى تثبيت المتطلبات: pip install -r requirements.txt")
        streamlit_proc.terminate()
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n⏹ إيقاف النظام...")
        streamlit_proc.terminate()
        print("✅ تم الإيقاف")


if __name__ == "__main__":
    main()
