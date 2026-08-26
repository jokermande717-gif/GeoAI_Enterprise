import json
import base64
import os
from datetime import datetime, timedelta
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.serialization import load_pem_private_key

def generate_license(hw_id: str, client_name: str, license_type: str = "TRIAL", days_valid: int = 14, private_key_path: str = "private_key.pem") -> str:
    """
    توليد ترخيص رقمي موقع بواسطة RSA-2048
    license_type: 'TRIAL' أو 'COMMERCIAL' أو 'ENTERPRISE'
    """
    if not os.path.exists(private_key_path):
        raise FileNotFoundError(f"لم يتم العثور على المفتاح الخاص: {private_key_path}")

    with open(private_key_path, "rb") as key_file:
        private_key = load_pem_private_key(key_file.read(), password=None)

    expiry_date = (datetime.now() + timedelta(days=days_valid)).strftime("%Y-%m-%d") if days_valid > 0 else "LIFETIME"

    payload = {
        "hw_id": hw_id.strip(),
        "client": client_name.strip(),
        "type": license_type.upper(),
        "expiry": expiry_date,
        "features": {
            "max_points": 100000 if license_type.upper() == "TRIAL" else -1,
            "export_ifc": True,
            "export_reb": True,
            "din_qes": True if license_type.upper() != "TRIAL" else False, # علامة مائية للنسخة التجريبية
            "watermark": True if license_type.upper() == "TRIAL" else False
        }
    }

    payload_bytes = json.dumps(payload, sort_keys=True).encode("utf-8")

    # التوقيع الرقمي للبيانات المشفرة
    signature = private_key.sign(
        payload_bytes,
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256()
    )

    license_packet = {
        "data": base64.b64encode(payload_bytes).decode("utf-8"),
        "sig": base64.b64encode(signature).decode("utf-8")
    }

    encoded_license = base64.b64encode(json.dumps(license_packet).encode("utf-8")).decode("utf-8")
    return encoded_license

if __name__ == "__main__":
    print("=== GeoAI Overworld | Lizenz-Generator ===")
    target_hw_id = input("أدخل Hardware-ID العميل: ").strip()
    target_client = input("اسم المكتب أو الشركة: ").strip()
    is_trial = input("هل هذا ترخيص تجريبي (14 يوم)؟ (y/n): ").strip().lower() == 'y'

    if is_trial:
        lic_key = generate_license(target_hw_id, target_client, license_type="TRIAL", days_valid=14)
        print("\n[✓] تم إنشاء ترخيص تجريبي (14 Tage Testversion):")
    else:
        lic_key = generate_license(target_hw_id, target_client, license_type="COMMERCIAL", days_valid=365)
        print("\n[✓] تم إنشاء ترخيص كامل (Vollversion 1 Jahr):")

    print("\n" + lic_key + "\n")