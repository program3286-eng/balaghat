"""
سجل الحركات Audit Log
"""
import json
from datetime import datetime
from utils.database import get_connection


def log_action(work_order_no, action_type, username, old_values=None, new_values=None, details=None):
    """تسجيل حركة في Audit Log"""
    try:
        conn = get_connection()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn.execute("""
            INSERT INTO audit_log (work_order_no, action_type, username, old_values, new_values, action_at, details)
            VALUES (?,?,?,?,?,?,?)
        """, (
            work_order_no,
            action_type,
            username,
            json.dumps(old_values, ensure_ascii=False) if old_values else None,
            json.dumps(new_values, ensure_ascii=False) if new_values else None,
            now,
            details,
        ))
        conn.commit()
        conn.close()
    except Exception:
        pass


def get_audit_log(limit=200, username_filter=None, action_filter=None):
    conn = get_connection()
    cur = conn.cursor()
    query = "SELECT * FROM audit_log WHERE 1=1"
    params = []
    if username_filter:
        query += " AND username=?"
        params.append(username_filter)
    if action_filter:
        query += " AND action_type=?"
        params.append(action_filter)
    query += " ORDER BY action_at DESC LIMIT ?"
    params.append(limit)
    cur.execute(query, params)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows
