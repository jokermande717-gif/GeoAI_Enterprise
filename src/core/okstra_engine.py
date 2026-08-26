import math

class OKSTRAEngine:
    @staticmethod
    def compute_cross_slope_and_drainage(speed_kmh, radius_m, width_m=7.5):
        q_min = 2.5
        q_calc = min(6.0, (speed_kmh**2) / (2.8 * radius_m)) if radius_m < 500 else q_min
        water_depth_mm = (width_m * 0.015) / math.sqrt(max(0.01, q_calc / 100.0))
        return {
            "querneigung_pct": q_calc,
            "min_querneigung": q_min,
            "water_depth_mm": water_depth_mm,
            "aquaplaning_risk": "NIEDRIG" if water_depth_mm < 2.5 else "HOCH"
        }
