"""
وظائف تشفير كلمات المرور - مستقلة عن Streamlit
"""
import hashlib, secrets

def hash_password(plain: str) -> str:
    salt = secrets.token_hex(16)
    key = hashlib.pbkdf2_hmac("sha256", plain.encode(), salt.encode(), 260_000)
    return f"pbkdf2$sha256${salt}${key.hex()}"

def verify_password(plain: str, stored: str) -> bool:
    try:
        _, algo, salt, key_hex = stored.split("$")
        key = hashlib.pbkdf2_hmac(algo, plain.encode(), salt.encode(), 260_000)
        return secrets.compare_digest(key.hex(), key_hex)
    except Exception:
        return False
