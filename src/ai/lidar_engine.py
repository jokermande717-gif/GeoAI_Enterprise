import math
import statistics
import os

class OfflineAILiDAREngine:
    """محرك الذكاء الاصطناعي الأوفلاين لمعالجة وتصنيف السحب النقطية الضخمة وكشف الانحرافات"""

    @staticmethod
    def parse_large_point_cloud(file_path, max_sample=5000):
        points = []
        ext = os.path.splitext(file_path)[1].lower()
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            for idx, line in enumerate(f):
                if idx >= max_sample:
                    break
                line = line.strip()
                if not line or line.startswith(('#', '//', '/*')):
                    continue
                parts = line.replace(',', ' ').replace(';', ' ').replace('\t', ' ').split()
                if len(parts) >= 3:
                    try:
                        # Auto-detect format (ID X Y Z or X Y Z)
                        if parts[0].replace('.', '', 1).replace('-', '', 1).isdigit():
                            p_id = f"PT-{idx+1:04d}"
                            e, n, z = float(parts[0]), float(parts[1]), float(parts[2])
                        else:
                            p_id = parts[0]
                            e, n, z = float(parts[1]), float(parts[2]), float(parts[3])
                        points.append({"id": p_id, "e": e, "n": n, "z": z})
                    except Exception:
                        continue
        return points

    @staticmethod
    def classify_points(points):
        if not points:
            return {"classified": [], "stats": {"total": 0, "ground": 0, "building": 0, "vegetation": 0, "noise": 0}}

        z_values = [p.get("z", 140.0) for p in points]
        mean_z = statistics.mean(z_values)
        stdev_z = statistics.stdev(z_values) if len(z_values) > 1 else 1.0

        classified = []
        counts = {"ground": 0, "building": 0, "vegetation": 0, "noise": 0}

        for p in points:
            z = p.get("z", 140.0)
            diff = z - mean_z

            if abs(diff) > 2.6 * stdev_z:
                cls_type = "Noise / Outlier"
                color = "#ef4444"
                counts["noise"] += 1
            elif diff < -0.35 * stdev_z:
                cls_type = "Ground (DGM)"
                color = "#10b981"
                counts["ground"] += 1
            elif diff > 0.75 * stdev_z:
                cls_type = "Building LoD2"
                color = "#00d2ff"
                counts["building"] += 1
            else:
                cls_type = "Vegetation"
                color = "#f59e0b"
                counts["vegetation"] += 1

            classified.append({
                "id": p["id"], "e": p["e"], "n": p["n"], "z": z,
                "class": cls_type, "color": color
            })

        stats = {
            "total": len(points),
            "ground": counts["ground"],
            "building": counts["building"],
            "vegetation": counts["vegetation"],
            "noise": counts["noise"]
        }
        return {"classified": classified, "stats": stats}

    @staticmethod
    def audit_measurement_errors(points):
        anomalies = []
        if len(points) < 3:
            return anomalies

        for i in range(min(500, len(points))):
            p = points[i]
            for j in range(i + 1, min(500, len(points))):
                q = points[j]
                d_horiz = math.sqrt((p["e"] - q["e"])**2 + (p["n"] - q["n"])**2)
                d_vert = abs(p["z"] - q["z"])

                if d_horiz < 2.5 and d_vert > 1.8:
                    anomalies.append({
                        "point_pair": f"{p['id']} - {q['id']}",
                        "type": "Geometrischer Steilsprung (dH > 1.8m)",
                        "error_mm": d_vert * 1000.0,
                        "status": "[ GROSS ERROR ]"
                    })
        return anomalies
