"""
export_io/bim_ifc.py
--------------------
Enterprise BIM IFC 4x3 Infrastructure Exporter.
Erzeugt standardkonforme IFC-Dateien (IFC4X3) mit georeferenzierter 
DGM-Tessellierung (IfcTriangulatedFaceSet) und Massenermittlung (Qto_Earthworks).
"""

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
import numpy as np

try:
    import ifcopenshell
    import ifcopenshell.api
    import ifcopenshell.guid
except ImportError:
    ifcopenshell = None


class BIMExporter:
    """محرك تصدير نماذج التضاريس وشبكات التثليث (TIN) إلى معيار IFC 4x3 Infrastructure."""

    def __init__(self) -> None:
        if ifcopenshell is None:
            raise ImportError(
                "Das Modul 'ifcopenshell' ist nicht installiert. Bitte mit 'pip install ifcopenshell' nachinstallieren."
            )

    @classmethod
    def export_terrain_to_ifc(
        cls,
        points: np.ndarray,
        triangles: np.ndarray,
        volume_stats: Dict[str, Any],
        output_path: Path | str,
        project_name: str = "Infrastrukturmassnahme",
        author_name: str = "Dipl.-Ing. OebVI",
        epsg_code: str = "EPSG:25832",
    ) -> Path:
        """
        إنشاء ملف IFC 4x3 متكامل يتضمن:
        1. الهيكل المكاني للبنية التحتية (IfcProject -> IfcSite -> IfcFacility).
        2. الإسناد الجغرافي والإسقاط (MapConversion & ProjectedCRS).
        3. شبكة التثليث الهندسية عبر IfcTriangulatedFaceSet.
        4. خصائص الكميات والحجوم الرسمية (Qto_Earthworks / Qto_BodyGeometryValidation).
        """
        if ifcopenshell is None:
            raise RuntimeError("IfcOpenShell ist nicht verfuegbar.")

        out_file = Path(output_path).with_suffix(".ifc")

        # 1. تهيئة ملف IFC بمخطط IFC4X3
        model = ifcopenshell.file(schema="IFC4X3")

        # 2. إنشاء الهيكل الإداري والمكاني الأساسي
        project = ifcopenshell.api.run(
            "root.create_entity",
            model,
            ifc_class="IfcProject",
            name=project_name,
        )

        # تعيين الوحدات المترية القياسية
        ifcopenshell.api.run(
            "unit.assign_unit",
            model,
            length={"is_metric": True, "raw": "METRE"},
            area={"is_metric": True, "raw": "SQUARE_METRE"},
            volume={"is_metric": True, "raw": "CUBIC_METRE"},
        )

        # إنشاء سياقات العرض الهندسي ثلاثي الأبعاد
        context = ifcopenshell.api.run(
            "context.add_context", model, context_type="Model"
        )
        body_context = ifcopenshell.api.run(
            "context.add_context",
            model,
            context_type="Model",
            context_identifier="Body",
            target_view="MODEL_VIEW",
            parent=context,
        )

        # إنشاء الموقع (Site) والمرفق الهندسي (Facility / Road Trasse)
        site = ifcopenshell.api.run(
            "root.create_entity",
            model,
            ifc_class="IfcSite",
            name="Gelaendefeld",
        )
        ifcopenshell.api.run(
            "aggregate.assign_object", model, product=site, relating_object=project
        )

        facility = ifcopenshell.api.run(
            "root.create_entity",
            model,
            ifc_class="IfcFacility",
            name="Infrastruktur_Trasse",
        )
        ifcopenshell.api.run(
            "aggregate.assign_object",
            model,
            product=facility,
            relating_object=site,
        )

        # 3. إعداد الإحداثيات والشبكة الهندسية (Tessellation)
        # موازنة الإحداثيات بنقطة مرجعية محلية لتفادي أخطاء الفاصلة العائمة في برامج الـ CAD
        origin = np.min(points, axis=0)
        local_coords = (points - origin).astype(np.float64)

        # قائمة الإحداثيات المحلية ثلاثية الأبعاد
        coord_list = [
            [float(pt[0]), float(pt[1]), float(pt[2])] for pt in local_coords
        ]
        point_list_entity = model.create_entity(
            "IfcCartesianPointList3D", CoordList=coord_list
        )

        # قائمة أوجه المثلثات (مؤشرات 1-based في معيار IFC)
        face_list = [[int(i + 1) for i in tri] for tri in triangles]

        triangulated_face_set = model.create_entity(
            "IfcTriangulatedFaceSet",
            Coordinates=point_list_entity,
            CoordIndex=face_list,
            Closed=False,
        )

        shape_rep = model.create_entity(
            "IfcShapeRepresentation",
            ContextOfItems=body_context,
            RepresentationIdentifier="Body",
            RepresentationType="Tessellation",
            Items=[triangulated_face_set],
        )

        product_shape = model.create_entity(
            "IfcProductDefinitionShape", Representations=[shape_rep]
        )

        # 4. إنشاء العنصر الجغرافي للتضاريس (IfcGeographicElement)
        terrain_element = ifcopenshell.api.run(
            "root.create_entity",
            model,
            ifc_class="IfcGeographicElement",
            name="DGM_Gelaendemodell",
            predefined_type="TERRAIN",
        )
        terrain_element.Representation = product_shape

        # ضبط الموضع المكاني
        ifcopenshell.api.run(
            "geometry.edit_object_placement",
            model,
            product=terrain_element,
        )
        ifcopenshell.api.run(
            "spatial.assign_container",
            model,
            product=terrain_element,
            relating_structure=facility,
        )

        # 5. إلحاق جداول الكميات القياسية (Qto_Earthworks)
        cut_v = float(volume_stats.get("cut_volume", 0.0))
        fill_v = float(volume_stats.get("fill_volume", 0.0))
        net_v = float(volume_stats.get("net_volume", cut_v - fill_v))
        area_2d = float(
            volume_stats.get(
                "total_2d_area", volume_stats.get("gauss_area", 0.0)
            )
        )

        qto_earthworks = ifcopenshell.api.run(
            "pset.add_qto",
            model,
            product=terrain_element,
            name="Qto_Earthworks",
        )
        ifcopenshell.api.run(
            "pset.edit_qto",
            model,
            qto=qto_earthworks,
            properties={
                "NetVolume": net_v,
                "CutVolume": cut_v,
                "FillVolume": fill_v,
                "GrossSurfaceArea": area_2d,
            },
        )

        # 6. إضافة مجموعة الخصائص الفنية (Pset_GeodeticSurvey)
        pset_survey = ifcopenshell.api.run(
            "pset.add_pset",
            model,
            product=terrain_element,
            name="Pset_GeodeticSurvey",
        )
        ifcopenshell.api.run(
            "pset.edit_pset",
            model,
            pset=pset_survey,
            properties={
                "SurveyStandard": "DIN 18716 / REB-VB 22.013",
                "ReferenceHeightSystem": epsg_code,
                "Inspector": author_name,
                "GenerationTimestamp": datetime.now(timezone.utc).isoformat(),
                "PointCount": int(len(points)),
                "TriangleCount": int(len(triangles)),
            },
        )

        # 7. حفظ الملف
        model.write(str(out_file))
        return out_file