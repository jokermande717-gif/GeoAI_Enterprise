import os
import sys
import io
import tarfile
import ctypes
import hashlib
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

def is_debugger_present():
    """كشف محاولات الهندسة العكسية وفحص الذاكرة"""
    try:
        if sys.platform == "win32":
            return ctypes.windll.kernel32.IsDebuggerPresent() != 0
    except Exception:
        pass
    return False

def extract_encrypted_payload(target_dir: str):
    if is_debugger_present():
        ctypes.windll.user32.MessageBoxW(0, "Security Violation: Debugger or Reverse Engineering Tool Detected.", "GeoAI Security Alert", 0x10)
        sys.exit(1)

    payload_file = "GeoAI_Encrypted_Payload.bin"
    key_file = "installer_key.bin"

    # التحقق من وجود الملفات التشفيرية
    if not os.path.exists(payload_file) or not os.path.exists(key_file):
        # البحث في المسار المؤقت للمثبت
        base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        payload_file = os.path.join(base_path, payload_file)
        key_file = os.path.join(base_path, key_file)

    try:
        with open(key_file, "rb") as f:
            key = f.read()

        with open(payload_file, "rb") as f:
            data = f.read()

        nonce = data[:12]
        ciphertext = data[12:]

        aesgcm = AESGCM(key)
        # فك التشفير مباشرة داخل الذاكرة RAM دون كتابة أرشيف غير مشفر على القرص
        decrypted_stream = aesgcm.decrypt(nonce, ciphertext, None)

        # استخراج المحتويات إلى مجلد التثبيت
        with tarfile.open(fileobj=io.BytesIO(decrypted_stream), mode="r:gz") as tar:
            tar.extractall(path=target_dir)

    except Exception as e:
        ctypes.windll.user32.MessageBoxW(0, f"Payload Decryption / Integrity Error: {str(e)}", "Installation Error", 0x10)
        sys.exit(1)

if __name__ == "__main__":
    install_path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.environ.get("ProgramFiles", "C:\\Program Files"), "GeoAI Overlord Enterprise")
    extract_encrypted_payload(install_path)
