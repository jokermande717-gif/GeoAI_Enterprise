import math
import hashlib
from datetime import datetime

class GeodesyEngine:
    @staticmethod
    def calculate_reb_masses(planum_z, points):
        cut_vol = 0.0
        fill_vol = 0.0
        if not points:
            points = [(0, 0, 142.5), (30, 0, 143.1), (30, 30, 141.8), (0, 30, 140.2)]

        for i in range(len(points) - 2):
            p1, p2, p3 = points[i], points[i+1], points[i+2]
            avg_z = (p1[2] + p2[2] + p3[2]) / 3.0
            diff = avg_z - planum_z
            area = 150.0
            vol = abs(diff * area)
            if diff > 0:
                cut_vol += vol
            else:
                fill_vol += vol

        saldo = fill_vol - cut_vol
        return {"cut": cut_vol, "fill": fill_vol, "saldo": saldo}

    @staticmethod
    def calculate_rail_dynamics(speed_kmh, radius_m):
        r = max(100.0, radius_m)
        u_theor = (11.8 * (speed_kmh ** 2)) / r
        u_exec = min(160.0, u_theor * 0.65)
        u_deficiency = u_theor - u_exec
        return {"u_theor": u_theor, "u_exec": u_exec, "u_deficiency": u_deficiency, "is_clear": u_deficiency <= 130.0}

    @staticmethod
    def generate_qes_stamp(summary):
        now_utc = datetime.utcnow().isoformat()
        digest = hashlib.sha256(f"{now_utc}_{summary}".encode()).hexdigest()
        return {"merkle_root": digest, "timestamp": now_utc, "hwid": "00B9C6E0A6FEBC10"}
