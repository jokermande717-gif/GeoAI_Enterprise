import os
import sys
import hashlib
import subprocess
import json

class SovereignLicenseEngine:
    SECRET_SALT = "GEOAI_SOVEREIGN_ENTERPRISE_2026_CORE_SALT_!#99"
    LICENSE_FILE = os.path.join(os.path.expanduser("~"), ".geoai_license.key")

    @staticmethod
    def get_hardware_fingerprint():
        """استخراج البصمة الفريدة لعتاد الجهاز الفعلي (HWID)"""
        try:
            # محاولة قراءة UUID اللوحة الأم عبر PowerShell/WMIC
            cmd = 'powershell "(Get-CimInstance -ClassName Win32_ComputerSystemProduct).UUID"'
            uuid = subprocess.check_output(cmd, shell=True).decode().strip()
            if not uuid or "UUID" in uuid:
                uuid = os.environ.get("COMPUTERNAME", "UNKNOWN_HOST") + "_" + os.environ.get("PROCESSOR_IDENTIFIER", "CPU")
        except Exception:
            uuid = os.environ.get("COMPUTERNAME", "GEOAI_NODE")

        raw_str = f"{uuid}_{SovereignLicenseEngine.SECRET_SALT}"
        hwid = hashlib.sha256(raw_str.encode()).hexdigest()[:16].upper()
        return hwid

    @staticmethod
    def generate_valid_key(hwid, customer_name="Enterprise User", tier="SOVEREIGN_ENTERPRISE"):
        """خوارزمية توليد المفتاح الصالح للترخيص بناءً على بصمة الـ HWID"""
        payload = f"{hwid}:{customer_name}:{tier}:{SovereignLicenseEngine.SECRET_SALT}"
        sig = hashlib.sha256(payload.encode()).hexdigest()[:24].upper()
        formatted_key = f"GEOAI-{hwid[:4]}-{sig[:4]}-{sig[4:8]}-{sig[8:12]}-{sig[12:16]}"
        return formatted_key

    @classmethod
    def verify_license(cls, input_key, hwid):
        """التحقق الرياضي المشفر من مطابقة مفتاح التفعيل مع عتاد الجهاز"""
        if not input_key or not hwid:
            return False
        clean_key = input_key.strip().upper()
        expected_key = cls.generate_valid_key(hwid)
        return clean_key == expected_key

    @classmethod
    def is_system_activated(cls):
        """فحص وجود وصحة ملف التفعيل المحفوظ على الجهاز"""
        if not os.path.exists(cls.LICENSE_FILE):
            return False
        try:
            with open(cls.LICENSE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            hwid = cls.get_hardware_fingerprint()
            return cls.verify_license(data.get("key", ""), hwid)
        except Exception:
            return False

    @classmethod
    def activate_system(cls, key):
        """حفظ وتفعيل المفتاح على الجهاز"""
        hwid = cls.get_hardware_fingerprint()
        if cls.verify_license(key, hwid):
            with open(cls.LICENSE_FILE, "w", encoding="utf-8") as f:
                json.dump({"key": key.strip().upper(), "hwid": hwid}, f)
            return True
        return False
