import os
import sys
import tarfile
import secrets
import hashlib
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

def build_encrypted_installer_payload(source_dir: str, output_enc_file: str):
    """
    يقوم بضغط كافة ملفات المنظومة وتشفيرها بنظام AES-256-GCM الصلب
    """
    print(">>> [1/3] Packing core distribution files into compressed stream...")
    tar_path = "temp_core.tar.gz"
    with tarfile.open(tar_path, "w:gz") as tar:
        tar.add(source_dir, arcname="GeoAI_Core")
        
    with open(tar_path, "rb") as f:
        data = f.read()
    
    # تنظيف الملف المؤقت
    os.remove(tar_path)

    print(">>> [2/3] Generating Cryptographic Key & AES-256-GCM Encryption...")
    # توليد مفتاح بطول 256 بت و Nonce عشوائي
    key = secrets.token_bytes(32)
    nonce = secrets.token_bytes(12)
    aesgcm = AESGCM(key)
    
    # تشفير البيانات مع إضافة Authentication Tag لمنع التلاعب
    ciphertext = aesgcm.encrypt(nonce, data, None)
    
    # حساب بصمة SHA-256 للملف المشفر
    file_hash = hashlib.sha256(ciphertext).hexdigest()

    print(">>> [3/3] Emitting encrypted container & cryptographic manifest...")
    # كتابة الحاوية المشفرة: [Nonce 12B] + [Ciphertext with Tag]
    with open(output_enc_file, "wb") as f:
        f.write(nonce + ciphertext)

    # حفظ المفتاح وسجل التشفير للمشغل المحمي
    with open("installer_key.bin", "wb") as f:
        f.write(key)

    print(f"\n[OK] ENCRYPTION COMPLETE:")
    print(f"  * Container : {output_enc_file} ({len(ciphertext)} bytes)")
    print(f"  * SHA-256   : {file_hash}")
    print(f"  * Key Status: 256-Bit Cryptographic Envelope Locked")

if __name__ == "__main__":
    src = "C:\\Users\\zxc12\\Desktop\\GeoAI_Enterprise"
    build_encrypted_installer_payload(src, "GeoAI_Encrypted_Payload.bin")
