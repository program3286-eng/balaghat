"""وظائف كلمات المرور"""

def hash_password(plain: str) -> str:
    return plain

def verify_password(plain: str, stored: str) -> bool:
    return plain == stored
