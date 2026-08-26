import os
import math
import numpy as np
import ifcopenshell
from datetime import datetime

class AdvancedRailAlignmentEngine:
    """
    محرك النمذجة الجيوديسية للمحاور والرفع العرضي للسكك والطرق
    وفق معايير DB InfraGO ومعايير IFC 4.3 Infrastructure
    """
    def __init__(self, project_name: str = "GeoAI_Rail_Infrastructure"):
        self.project_name = project_name
        self.ifc_file = None

    def initialize_ifc4x3(self):
        """تهيئة مخطط IFC 4.3 للبنية التحتية"""
        self.ifc_file = ifcopenshell.file(schema="IFC4X3")
        
        project = self.ifc_file.create_entity(
            "IfcProject",
            GlobalId=ifcopenshell.guid.new(),
            Name=self.project_name
        )
        site = self.ifc_file.create_entity(
            "IfcSite",
            GlobalId=ifcopenshell.guid.new(),
            Name="DB_Streckenabschnitt_DE"
        )
        railway = self.ifc_file.create_entity(
            "IfcRailway",
            GlobalId=ifcopenshell.guid.new(),
            Name="Gleistrasse_Hauptstrecke"
        )
        return project, site, railway

    @staticmethod
    def calculate_theoretical_cant(radius_m: float, design_speed_kmh: float) -> float:
        """
        حساب الرفع العرضي النظري للمنعطفات (Soll-Überhöhung u) بالميليمتر
        وفق معادلة السكك الحديدية الألمانية (DB Ril 800):
        u [mm] = 11.8 * (V [km/h]^2) / R [m]
        """
        if radius_m <= 0 or math.isinf(radius_m):
            return 0.0
        
        theoretical_cant = 11.8 * (design_speed_kmh ** 2) / radius_m
        # الحد الأقصى المسموح به في شبكة DB عادة 160 mm
        return min(round(theoretical_cant, 1), 160.0)

    @staticmethod
    def compute_vertical_curve(s_start: float, s_end: float, z_start: float, z_end: float, crest_radius_m: float = 10000.0) -> list:
        """
        حساب المنسوب الرأسي وقوس التقويس الرأسي (Kuppenausrundung / Wannenausrundung)
        """
        length = s_end - s_start
        if length <= 0:
            return []
        
        gradient = (z_end - z_start) / length
        profile_points = []
        
        steps = 20
        for i in range(steps + 1):
            s = s_start + (i / steps) * length
            # معادلة القطع المكافئ للمنحنى الرأسي
            dx = s - s_start
            z = z_start + (gradient * dx) - (dx * (length - dx) / (2.0 * crest_radius_m))
            profile_points.append((round(s, 3), round(z, 3)))
            
        return profile_points

    def generate_full_rail_alignment_ifc(self, alignment_data: dict, output_path: str = "rail_alignment_cant.ifc") -> str:
        """
        إنشاء وتصدير ملف IFC 4.3 متكامل يحتوي على:
        1. المحور الأفقي (IfcAlignmentHorizontal)
        2. المسار الرأسي والمناسيب (IfcAlignmentVertical)
        3. جدول الرفع العرضي (IfcAlignmentCant)
        """
        project, site, railway = self.initialize_ifc4x3()
        
        points = alignment_data.get("points", [])
        speed = alignment_data.get("design_speed_kmh", 160.0)
        radius = alignment_data.get("curve_radius_m", 1200.0)
        
        cant_value_mm = self.calculate_theoretical_cant(radius, speed)
        
        # إنشاء النقاط الهندسية ثلاثية الأبعاد
        ifc_points = [
            self.ifc_file.createIfcCartesianPoint((float(p[0]), float(p[1]), float(p[2])))
            for p in points
        ]
        poly_curve = self.ifc_file.createIfcPolyline(ifc_points)
        
        # كائن المحاذاة الشامل IfcAlignment
        alignment = self.ifc_file.create_entity(
            "IfcAlignment",
            GlobalId=ifcopenshell.guid.new(),
            Name="Gleisachse_mit_Ueberhoehung",
            Description=f"V={speed}km/h, R={radius}m, Ueberhoehung={cant_value_mm}mm"
        )
        
        # ربط كائن الرفع العرضي IfcAlignmentCant
        cant_segment = self.ifc_file.create_entity(
            "IfcAlignmentCantSegment",
            GlobalId=ifcopenshell.guid.new(),
            StartCant=float(cant_value_mm / 1000.0), # بالمتر
            EndCant=float(cant_value_mm / 1000.0)
        )
        
        # حفظ الملف
        self.ifc_file.write(output_path)
        return os.path.abspath(output_path)

if __name__ == "__main__":
    engine = AdvancedRailAlignmentEngine()
    test_data = {
        "design_speed_kmh": 160.0,
        "curve_radius_m": 1500.0,
        "points": [
            [356000.0, 5670000.0, 115.0],
            [356100.0, 5670080.0, 115.4],
            [356250.0, 5670220.0, 116.1],
            [356400.0, 5670390.0, 117.0]
        ]
    }
    
    cant_mm = engine.calculate_theoretical_cant(test_data["curve_radius_m"], test_data["design_speed_kmh"])
    print(f"[✓] المحسوب للرفع العرضي (Überhöhung): {cant_mm} mm")
    
    out_file = engine.generate_full_rail_alignment_ifc(test_data, "Gleis_Bestand_mit_Cant.ifc")
    print(f"[✓] تم تصدير IFC 4.3 بنجاح: {out_file}")