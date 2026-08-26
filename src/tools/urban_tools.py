import math

class BuildingObject:
    def __init__(self, points, height=25.0, name="Gebäude"):
        self.points = points
        self.height = height
        self.name = name

    def compute_solar_potential(self):
        # حساب المساحة السطحية للسقف وتقدير إنتاج الكهرباء السنوي
        n = len(self.points)
        area = 0.0
        for i in range(n):
            j = (i + 1) % n
            area += self.points[i][0] * self.points[j][1]
            area -= self.points[j][0] * self.points[i][1]
        roof_area_m2 = (abs(area) / 2.0) * 8.5
        solar_capacity_kwp = (roof_area_m2 * 0.7) * 0.20 # 200W/m2
        annual_kwh = solar_capacity_kwp * 1050.0 # كفاءة ألمانيا الوسطى
        return {"roof_m2": roof_area_m2, "kwp": solar_capacity_kwp, "annual_kwh": annual_kwh}

class RoadObject:
    def __init__(self, points, width=14.0, name="Straße"):
        self.points = points
        self.width = width
        self.name = name

class MarkerPointObject:
    def __init__(self, x, y, lat, lon, utm_e, utm_n, name="TP-Neu"):
        self.x = x
        self.y = y
        self.lat = lat
        self.lon = lon
        self.utm_e = utm_e
        self.utm_n = utm_n
        self.name = name
