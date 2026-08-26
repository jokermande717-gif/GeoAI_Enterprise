import json
import base64
import os
import sys
import subprocess
from datetime import datetime
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.serialization import load_pem_public_key

def get_resource_path(relative_path: str) -> str:
    """الحصول على المسار الصحيح للملف سواء أثناء التطوير أو داخل حزمة PyInstaller"""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

class LicenseManager:
    """
    نظام إدارة التراخيص الرقمية المشفرة بـ RSA-2048
    GeoAI Overworld - Deutschland Edition
    """
    def __init__(self, public_key_path: str = "public_key.pem", license_file_path: str = "license.key"):
        self.public_key_path = get_resource_path(public_key_path)
        self.license_file_path = license_file_path
        self.license_info = None

    @staticmethod
    def get_hardware_id() -> str:
        """استخراج المعرف العتادي الفريد للجهاز عبر WMI لنظام Windows"""
        try:
            cmd = "wmic csproduct get uuid"
            output = subprocess.check_output(cmd, shell=True).decode().split()
            if len(output) >= 2:
                return output[1].strip()
        except Exception:
            pass
        return "GENERIC-DE-HWID-2026"

    def verify_license_string(self, license_string: str) -> tuple[bool, str, dict]:
        """
        التحقق الرياضي من صحة التوقيع الرقمي ومطابقة الـ Hardware-ID وصلاحية التاريخ
        """
        if not os.path.exists(self.public_key_path):
            return False, f"Öffentlicher Schlüssel fehlt: {self.public_key_path}", {}

        try:
            raw_json = base64.b64decode(license_string.strip().encode("utf-8")).decode("utf-8")
            license_packet = json.loads(raw_json)
            
            payload_bytes = base64.b64decode(license_packet["data"].encode("utf-8"))
            signature = base64.b64decode(license_packet["sig"].encode("utf-8"))

            with open(self.public_key_path, "rb") as kf:
                public_key = load_pem_public_key(kf.read())

            # التحقق من توقيع RSA-PSS
            public_key.verify(
                signature,
                payload_bytes,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )

            data = json.loads(payload_bytes.decode("utf-8"))

            # 1. التحقق من تطابق العتاد
            current_hwid = self.get_hardware_id()
            lic_hwid = data.get("hw_id")
            if lic_hwid != "ANY" and lic_hwid != current_hwid:
                return False, f"Hardware-ID nicht übereinstimmend (Erwartet: {lic_hwid}, Aktuell: {current_hwid})", {}

            # 2. التحقق من تاريخ انتهاء الصلاحية
            expiry = data.get("expiry")
            if expiry and expiry != "LIFETIME":
                exp_date = datetime.strptime(expiry, "%Y-%m-%d")
                if datetime.now() > exp_date:
                    return False, f"Die Lizenz ist am {expiry} abgelaufen.", {}

            self.license_info = data
            return True, "Lizenz ist gültig.", data

        except Exception as e:
            return False, f"Ungültige Lizenzsignatur: {str(e)}", {}

    def activate_license(self, license_string: str) -> tuple[bool, str]:
        """التحقق من المفتاح وحفظه محلياً في ملف license.key"""
        valid, msg, data = self.verify_license_string(license_string)
        if valid:
            try:
                with open(self.license_file_path, "w", encoding="utf-8") as f:
                    f.write(license_string.strip())
                return True, "Lizenz erfolgreich aktiviert und gespeichert."
            except Exception as e:
                return False, f"Fehler beim Speichern der Lizenzdatei: {str(e)}"
        return False, msg

    @classmethod
    def is_system_licensed(cls, public_key_path: str = "public_key.pem", license_file: str = "license.key") -> tuple[bool, dict]:
        """
        دالة الفحص الرئيسية عند بدء تشغيل البرنامج
        تتحقق من وجود ملف الترخيص وصحته بدون الحاجة لإنشاء كائن مسبقاً
        """
        if not os.path.exists(license_file):
            return False, {}

        try:
            with open(license_file, "r", encoding="utf-8") as f:
                key_str = f.read().strip()

            if not key_str:
                return False, {}

            mgr = cls(public_key_path=public_key_path, license_file_path=license_file)
            valid, _, data = mgr.verify_license_string(key_str)
            return valid, data
        except Exception:
            return False, {}