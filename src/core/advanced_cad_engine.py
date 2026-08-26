import os
import math
import csv

class AdvancedCADEngine:
    @staticmethod
    def parse_survey_file(file_path):
        points = []
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                parts = [p.strip() for p in line.replace(';', ',').replace('\t', ',').split(',')]
                if len(parts) >= 3:
                    try:
                        p_id = parts[0]
                        e = float(parts[1])
                        n = float(parts[2])
                        z = float(parts[3]) if len(parts) > 3 else 140.000
                        code = parts[4] if len(parts) > 4 else "Vermessung"
                        points.append({"id": p_id, "e": e, "n": n, "z": z, "code": code})
                    except Exception:
                        continue
        return points

    @staticmethod
    def compute_longitudinal_profile(road_pts, base_elevation=140.0):
        stations = []
        cum_dist = 0.0
        for i in range(len(road_pts)):
            if i > 0:
                dx = road_pts[i][0] - road_pts[i-1][0]
                dy = road_pts[i][1] - road_pts[i-1][1]
                dist = math.sqrt(dx*dx + dy*dy) * 3.2
                cum_dist += dist

            terrain_z = base_elevation + math.sin(cum_dist * 0.02) * 2.8 + (cum_dist * 0.004)
            design_z = base_elevation + 0.85 + (cum_dist * 0.005)
            diff_z = design_z - terrain_z
            stations.append({
                "station": cum_dist,
                "terrain_z": terrain_z,
                "design_z": design_z,
                "diff_z": diff_z,
                "gradient_pct": 0.50
            })
        return stations

    @staticmethod
    def generate_full_da45(points, cut_m3, fill_m3):
        lines = [
            "DA45 22.013 REB-VB VOB/C 2026.1",
            "00 00000000 0000 000 000000",
            f"01 URB_PRJ 2026-08-26 CUT={int(cut_m3)} FILL={int(fill_m3)}"
        ]
        for i, pt in enumerate(points):
            lines.append(f"45 {i+1:06d} {pt['e']:12.3f} {pt['n']:12.3f} {pt['z']:8.3f}")
        lines.append("99 00000000")
        return "\n".join(lines)

    @staticmethod
    def generate_dxf_3d(buildings, roads, markers):
        dxf = [
            "0\nSECTION\n2\nHEADER\n0\nENDSEC",
            "0\nSECTION\n2\nENTITIES"
        ]
        # DXF Markers
        for m in markers:
            dxf.append(f"0\nPOINT\n8\nVERMESSUNGSPUNKTE\n10\n{m.utm_e}\n20\n{m.utm_n}\n30\n142.0")
            dxf.append(f"0\nTEXT\n8\nPUNKT_BESCHRIFTUNG\n10\n{m.utm_e + 1.0}\n20\n{m.utm_n + 1.0}\n30\n142.0\n40\n1.5\n1\n{m.name}")

        # DXF Roads
        for r in roads:
            if len(r.points) >= 2:
                for i in range(len(r.points) - 1):
                    dxf.append(f"0\nLINE\n8\nSTRASSEN_ACHSE\n10\n{r.points[i][0]}\n20\n{r.points[i][1]}\n30\n142.0\n11\n{r.points[i+1][0]}\n21\n{r.points[i+1][1]}\n31\n142.0")

        dxf.append("0\nENDSEC\n0\nEOF")
        return "\n".join(dxf)

    @staticmethod
    def generate_landxml(roads):
        xml = [
            '<?xml version="1.0" encoding="utf-8"?>',
            '<LandXML version="1.2" date="2026-08-26">',
            '  <Alignments name="Trassen_Projekt">',
            '    <Alignment name="Hauptachse_1" length="450.0">'
        ]
        for r in roads:
            for i in range(len(r.points) - 1):
                xml.append(f'      <CoordGeom><Line><Start>{r.points[i][0]} {r.points[i][1]}</Start><End>{r.points[i+1][0]} {r.points[i+1][1]}</End></Line></CoordGeom>')
        xml.append('    </Alignment>\n  </Alignments>\n</LandXML>')
        return "\n".join(xml)
