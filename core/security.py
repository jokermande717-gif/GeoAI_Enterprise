import json
import base64
import uuid
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.serialization import load_pem_public_key

PUBLIC_KEY_PEM = """-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAxV5ze90PGwTOyS9KQty1
9rGp296PU/28Uy4LjJ9H/UnnRdekMDzuHZvI3ZGB7Qe7dS5sK7qUBc8VxFhABI+w
Ezenf+YMVSUUjEIoyE0lmoUrNk+ONQdXjKHDX+/FbfQV3vvGY+WlIyQUF3DdV92j
S6VXX8m9lKVAqPKqZvnlCsOk7G9CpJJon1EhZi1HFwQeS6rSsZ8bXNYcYzZg2lfH
aq4desJ3hMxx7Psl4jkznXc5nedZor9VYhZX3pnSjQOB5d2oOTB8OvVLZhApGbgH
n8dBRfRh9nYwFM2WPBP+X0s1bjz4l6BQjgmQFjS2UagHOVXUnA/nHHNKcQcnLB7I
awIDAQAB
-----END PUBLIC KEY-----"""

def get_hardware_id():
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, str(uuid.getnode()))).upper()

def verify_license_file(lic_text: str):
    try:
        packet = json.loads(base64.b64decode(lic_text.strip()).decode("utf-8"))
        payload_bytes = base64.b64decode(packet["data"])
        signature = base64.b64decode(packet["sig"])

        pub_key = load_pem_public_key(PUBLIC_KEY_PEM.encode("utf-8"))
        pub_key.verify(
            signature,
            payload_bytes,
            padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
            hashes.SHA256()
        )
        return True, json.loads(payload_bytes.decode("utf-8"))
    except Exception as e:
        return False, str(e)
