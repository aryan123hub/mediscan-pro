import hashlib
import os

def hash_password(password: str) -> str:
    """Password ko secure hash mein convert karta hai."""
    # Ek random salt generate karo (taaki har password alag dikhe)
    salt = os.urandom(16)
    # PBKDF2 algorithm se hash karo (Industry standard)
    pwd_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
    # Salt aur Hash ko combine karke return karo
    return salt.hex() + ":" + pwd_hash.hex()

def verify_password(stored_password: str, provided_password: str) -> bool:
    """Check karta hai ki entered password database wale password se match karta hai ya nahi."""
    try:
        # Agar database mein purana plain-text password hai (backward compatibility)
        if ":" not in stored_password:
            return stored_password == provided_password
        
        salt_hex, hash_hex = stored_password.split(':')
        salt = bytes.fromhex(salt_hex)
        # Entered password ko wahi salt dekar hash karo
        pwd_hash = hashlib.pbkdf2_hmac('sha256', provided_password.encode('utf-8'), salt, 100000)
        return pwd_hash.hex() == hash_hex
    except Exception:
        return False