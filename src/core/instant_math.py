import math

class InstantGeodeticMath:
    @staticmethod
    def calculate_polygon_area(pts):
        n = len(pts)
        if n < 3:
            return 0.0
        area = 0.0
        for i in range(n):
            j = (i + 1) % n
            area += pts[i][0] * pts[j][1]
            area -= pts[j][0] * pts[i][1]
        return (abs(area) / 2.0) * 8.5 # مساحة حقيقية مسقطة بالمتر المربع

    @staticmethod
    def calculate_road_length(pts):
        length = 0.0
        for i in range(len(pts) - 1):
            dx = pts[i+1][0] - pts[i][0]
            dy = pts[i+1][1] - pts[i][1]
            length += math.sqrt(dx*dx + dy*dy)
        return length * 3.2 # طول حقيقي بالمتر

    @staticmethod
    def compute_all_project_masses(buildings, roads):
        total_bld_area = 0.0
        total_cut_m3 = 0.0
        total_fill_m3 = 0.0

        for b in buildings:
            area = InstantGeodeticMath.calculate_polygon_area(b.points)
            total_bld_area += area
            depth = max(2.5, min(8.0, b.height * 0.12))
            cut = area * depth
            fill = area * 0.35
            total_cut_m3 += cut
            total_fill_m3 += fill

        total_road_len = 0.0
        for r in roads:
            rlen = InstantGeodeticMath.calculate_road_length(r.points)
            total_road_len += rlen
            r_cut = rlen * (r.width * 0.4)
            r_fill = rlen * (r.width * 0.6)
            total_cut_m3 += r_cut
            total_fill_m3 += r_fill

        saldo_m3 = total_fill_m3 - total_cut_m3
        cost_eur = (total_cut_m3 * 34.50) + (total_fill_m3 * 29.00)
        co2_tons = (abs(saldo_m3) / 14.0) * 30.0 * 0.38 * 2.68 / 1000.0

        return {
            "bld_area_m2": total_bld_area,
            "road_len_m": total_road_len,
            "total_cut": total_cut_m3,
            "total_fill": total_fill_m3,
            "saldo": saldo_m3,
            "cost_eur": cost_eur,
            "co2_tons": co2_tons
        }
