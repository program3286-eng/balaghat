"""
سيرفر FastAPI - PWA
  /          → صفحة التثبيت الجميلة
  /app/*     → Streamlit (النظام الفعلي)
  /static/*  → ملفات PWA (أيقونات، manifest، SW)
"""
import os
import httpx
from fastapi import FastAPI, Request, Response
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse

BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")

STREAMLIT_PORT = int(os.environ.get("STREAMLIT_PORT", "8501"))
STREAMLIT_URL  = f"http://127.0.0.1:{STREAMLIT_PORT}"

app = FastAPI(title="نظام إدارة البلاغات", docs_url=None, redoc_url=None)

# ─── الملفات الثابتة ───
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


# ─── الجذر → صفحة التثبيت ───
@app.get("/")
async def install_page():
    return FileResponse(
        os.path.join(STATIC_DIR, "install.html"),
        media_type="text/html"
    )


# ─── PWA الملفات المطلوبة ───
@app.get("/manifest.json")
async def manifest():
    return FileResponse(
        os.path.join(STATIC_DIR, "manifest.json"),
        media_type="application/manifest+json"
    )


@app.get("/service-worker.js")
async def service_worker():
    return FileResponse(
        os.path.join(STATIC_DIR, "service-worker.js"),
        media_type="application/javascript",
        headers={"Service-Worker-Allowed": "/"}
    )


@app.get("/offline.html")
async def offline():
    return FileResponse(os.path.join(STATIC_DIR, "offline.html"))


# ─── /app و /app/* → Proxy إلى Streamlit ───
@app.api_route(
    "/app",
    methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD", "PATCH"]
)
@app.api_route(
    "/app/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD", "PATCH"]
)
async def proxy_app(request: Request, path: str = ""):
    return await _proxy(request, path)


# ─── باقي المسارات (WebSocket وملفات Streamlit الداخلية) ───
@app.api_route(
    "/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD", "PATCH"]
)
async def proxy_all(request: Request, path: str = ""):
    # تجاهل المسارات الثابتة المعالجة فوق
    if path in ("manifest.json", "service-worker.js", "offline.html"):
        return Response(status_code=404)
    return await _proxy(request, path)


async def _proxy(request: Request, path: str):
    """تمرير الطلب إلى Streamlit"""
    # إزالة /app من بداية المسار
    clean_path = path.lstrip("/")
    if clean_path.startswith("app/"):
        clean_path = clean_path[4:]
    elif clean_path == "app":
        clean_path = ""

    target_url = f"{STREAMLIT_URL}/{clean_path}"
    qs = request.url.query
    if qs:
        target_url += f"?{qs}"

    headers = {k: v for k, v in request.headers.items()
               if k.lower() not in ("host", "content-length")}

    body = await request.body()

    async with httpx.AsyncClient(timeout=30) as client:
        try:
            resp = await client.request(
                method=request.method,
                url=target_url,
                headers=headers,
                content=body,
                follow_redirects=True,
            )
        except httpx.ConnectError:
            return HTMLResponse(
                _loading_page(),
                status_code=503
            )

    resp_headers = {k: v for k, v in resp.headers.items()
                    if k.lower() not in (
                        "content-encoding", "content-length",
                        "transfer-encoding", "connection"
                    )}

    content_type = resp.headers.get("content-type", "")

    if "text/html" in content_type:
        html = resp.text
        inject = _pwa_meta() + _pwa_js()
        html = html.replace("</head>", inject + "</head>", 1) if "</head>" in html else inject + html
        return HTMLResponse(html, status_code=resp.status_code, headers=resp_headers)

    return Response(
        content=resp.content,
        status_code=resp.status_code,
        headers=resp_headers,
        media_type=content_type,
    )


def _loading_page() -> str:
    return """<!DOCTYPE html><html lang="ar" dir="rtl">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<link href="https://fonts.googleapis.com/css2?family=Tajawal:wght@700&display=swap" rel="stylesheet">
<style>
body{margin:0;background:linear-gradient(160deg,#1a3c6e,#0d2447);
color:#fff;font-family:'Tajawal',sans-serif;height:100vh;
display:flex;flex-direction:column;align-items:center;justify-content:center;gap:20px}
.sp{width:52px;height:52px;border:4px solid rgba(255,255,255,.15);
border-top-color:#f0c040;border-radius:50%;animation:s .9s linear infinite}
@keyframes s{to{transform:rotate(360deg)}}
p{font-size:1.1rem;opacity:.85;margin:0}
small{opacity:.5;font-size:.85rem}
</style></head><body>
<div style="font-size:60px">🔧</div>
<div class="sp"></div>
<p>جاري تشغيل النظام...</p>
<small>لحظة واحدة ثم أعد المحاولة</small>
<script>setTimeout(()=>location.reload(),3000)</script>
</body></html>"""


def _pwa_meta() -> str:
    return """
  <meta name="mobile-web-app-capable" content="yes">
  <meta name="apple-mobile-web-app-capable" content="yes">
  <meta name="apple-mobile-web-app-title" content="بلاغات">
  <meta name="theme-color" content="#1a3c6e">
  <link rel="manifest" href="/manifest.json">
  <link rel="apple-touch-icon" href="/static/icons/icon-192x192.png">
"""


def _pwa_js() -> str:
    return """
  <script>
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/service-worker.js', {scope: '/'})
      .catch(e => console.warn('SW:', e));
  }
  </script>
"""
