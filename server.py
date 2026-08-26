import os
import json
import base64
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.serialization import load_pem_private_key

app = FastAPI(title="GeoAI Overworld Licensing API")

# السماح بطلبات الويب من الموقع
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class TrialRequest(BaseModel):
    company: str
    email: EmailStr
    hw_id: str

def create_rsa_license(hw_id: str, client_name: str, days: int = 14) -> str:
    private_key_path = "private_key.pem"
    if not os.path.exists(private_key_path):
        raise FileNotFoundError("private_key.pem missing on server.")

    with open(private_key_path, "rb") as kf:
        private_key = load_pem_private_key(kf.read(), password=None)

    expiry = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")
    payload = {
        "hw_id": hw_id.strip(),
        "client": client_name.strip(),
        "type": "TRIAL",
        "expiry": expiry,
        "features": {"max_points": 100000, "export_ifc": True, "export_reb": True, "watermark": True}
    }
    
    payload_bytes = json.dumps(payload, sort_keys=True).encode("utf-8")
    signature = private_key.sign(
        payload_bytes,
        padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
        hashes.SHA256()
    )
    
    packet = {
        "data": base64.b64encode(payload_bytes).decode("utf-8"),
        "sig": base64.b64encode(signature).decode("utf-8")
    }
    return base64.b64encode(json.dumps(packet).encode("utf-8")).decode("utf-8")

@app.post("/api/request-trial")
async def request_trial(req: TrialRequest):
    try:
        # 1. توليد المفتاح المشفر
        license_key = create_rsa_license(req.hw_id, req.company, days=14)
        
        # 2. حفظ بيانات العميل في سجل محلي لمتابعة المبيعات
        log_entry = f"{datetime.now().isoformat()} | {req.company} | {req.email} | HWID: {req.hw_id}\n"
        with open("leads_audit.log", "a", encoding="utf-8") as f:
            f.write(log_entry)

        # 3. إرجاع المفتاح مباشرة للواجهة
        return {
            "status": "success",
            "message": "Lizenz erfolgreich generiert.",
            "license_key": license_key,
            "valid_until": (datetime.now() + timedelta(days=14)).strftime("%d.%m.%Y")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)