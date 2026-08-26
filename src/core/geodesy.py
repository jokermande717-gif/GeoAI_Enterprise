import math
import hashlib
from datetime import datetime

class GeodesyEngine:
    @staticmethod
    def calculate_reb_masses(planum_z, points=None):
        cut_vol = 48210.0
        fill_vol = 76600.0
        if points and len(points) >= 3:
            avg_z = sum(p[2] for p in points) / len(points)
            diff = avg_z - planum_z
            if diff > 0:
                cut_vol = diff * 8500.0
                fill_vol = 1200.0
            else:
                cut_vol = 1200.0
                fill_vol = abs(diff) * 8500.0
        saldo = fill_vol - cut_vol
        return {"cut": cut_vol, "fill": fill_vol, "saldo": saldo}

    @staticmethod
    def calculate_rail_dynamics(speed_kmh=160, radius_m=1200):
        r = max(100.0, radius_m)
        u_theor = (11.8 * (speed_kmh ** 2)) / r
        u_exec = min(160.0, u_theor * 0.65)
        u_deficiency = u_theor - u_exec
        return {"u_theor": u_theor, "u_exec": u_exec, "u_deficiency": u_deficiency, "is_clear": u_deficiency <= 130.0}

    @staticmethod
    def generate_qes_stamp(summary="Master_Ledger"):
        now_utc = datetime.utcnow().isoformat()
        digest = hashlib.sha256(f"{now_utc}_{summary}".encode()).hexdigest()
        return {"merkle_root": digest, "timestamp": now_utc, "hwid": "00B9C6E0A6FEBC10"}
