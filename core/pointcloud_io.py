"""
core/pointcloud_io.py
---------------------
محرك متقدم لإدارة وتدفق سحب النقاط بصيغ LAS و LAZ (1.2 إلى 1.4).
- دعم فك الضغط التلقائي لملفات LAZ المضغوطة (LazBackend عبر laspy/lazrs).
- تصفية واستخراج الطبقات المصنفة وفق معايير ASPRS القياسية (Ground, Low Veg, High Veg, Buildings).
- تحسين استهلاك الذاكرة عبر القراءة بالتدفق (Chunked Streaming).
"""

from dataclasses import dataclass
from enum import IntEnum
from pathlib import Path
from typing import Dict, Generator, List, Optional, Tuple
import numpy as np
import laspy


class ASPRSClass(IntEnum):
    """رموز التصنيف القياسية المعتمدة من ASPRS لملفات الليزر والدرون."""
    CREATED_NEVER_CLASSIFIED = 0
    UNCLASSIFIED = 1
    GROUND = 2
    LOW_VEGETATION = 3
    MEDIUM_VEGETATION = 4
    HIGH_VEGETATION = 5
    BUILDING = 6
    LOW_POINT_NOISE = 7
    MODEL_KEY_POINT = 8
    WATER = 9
    ROAD_SURFACE = 11
    OVERLAP_POINTS = 12


@dataclass
class PointCloudMetadata:
    total_points: int
    point_format_id: int
    version: str
    scales: np.ndarray
    offsets: np.ndarray
    bounds_min: np.ndarray
    bounds_max: np.ndarray
    has_colors: bool
    has_intensity: bool
    classification_counts: Dict[int, int]


class PointCloudIOEngine:
    """محرك القراءة والكتابة والفلترة عالي الأداء لملفات LAS/LAZ."""

    @staticmethod
    def inspect_file(file_path: Path) -> PointCloudMetadata:
        """فحص سريع لترويسة الملف (Header) دون تحميل ملايين النقاط في الذاكرة."""
        with laspy.open(file_path) as reader:
            header = reader.header
            bounds_min = np.array([header.x_min, header.y_min, header.z_min])
            bounds_max = np.array([header.x_max, header.y_max, header.z_max])
            scales = np.array(header.scales)
            offsets = np.array(header.offsets)
            
            # فحص نوع التنسيق للألوان والشدة
            has_colors = header.point_format.has_color
            has_intensity = "intensity" in header.point_format.dimension_names

            # محاولة قراءة جدول إحصاءات التصنيف إن وجد في ترويسة LAS 1.4
            cls_counts = {}
            if hasattr(header, "number_of_points_by_return"):
                pass

        return PointCloudMetadata(
            total_points=header.point_count,
            point_format_id=header.point_format.id,
            version=f"{header.version.major}.{header.version.minor}",
            scales=scales,
            offsets=offsets,
            bounds_min=bounds_min,
            bounds_max=bounds_max,
            has_colors=has_colors,
            has_intensity=has_intensity,
            classification_counts=cls_counts,
        )

    @classmethod
    def read_las_laz(
        cls, 
        file_path: Path, 
        allowed_classes: Optional[List[int]] = None
    ) -> Tuple[np.ndarray, np.ndarray, Optional[np.ndarray]]:
        """
        قراءة بيانات سحابة النقاط بالكامل.
        المخرجات: (مصفوفة الإحداثيات XYZ، مصفوفة التصنيف، مصفوفة الألوان RGB إن وُجدت).
        """
        las = laspy.read(file_path)
        
        # استخراج الإحداثيات الدقيقة (Scaled Coordinates)
        x = las.x
        y = las.y
        z = las.z
        coords = np.vstack((x, y, z)).T
        
        # استخراج التصنيفات
        classifications = np.array(las.classification)

        # استخراج الألوان إن توفرت
        colors = None
        if hasattr(las, "red") and hasattr(las, "green") and hasattr(las, "blue"):
            # تحويل القيم من 16-bit إلى 8-bit إذا لزم الأمر
            r = (las.red >> 8 if las.red.max() > 255 else las.red).astype(np.uint8)
            g = (las.green >> 8 if las.green.max() > 255 else las.green).astype(np.uint8)
            b = (las.blue >> 8 if las.blue.max() > 255 else las.blue).astype(np.uint8)
            colors = np.vstack((r, g, b)).T

        # تطبيق فلترة الطبقات (مثل استخراج الأرض Ground فقط لحساب الـ DGM)
        if allowed_classes is not None:
            mask = np.isin(classifications, allowed_classes)
            coords = coords[mask]
            classifications = classifications[mask]
            if colors is not None:
                colors = colors[mask]

        return coords, classifications, colors

    @classmethod
    def write_classified_laz(
        cls,
        output_path: Path,
        coords: np.ndarray,
        classifications: np.ndarray,
        colors: Optional[np.ndarray] = None,
        epsg_code: Optional[str] = None
    ) -> None:
        """
        تصدير وحفظ سحابة النقاط المصنفة بصيغة LAZ المضغوطة أو LAS القياسية.
        """
        point_format = 3 if colors is not None else 2
        header = laspy.LasHeader(point_format=point_format, version="1.4")
        
        # ضبط المقاييس والإزاحة لمنع فقدان الدقة العشرية
        header.offsets = np.min(coords, axis=0)
        header.scales = np.array([0.001, 0.001, 0.001])  # دقة 1 ملليمتر

        # كتابة نظام الإحداثيات CRS إذا تم توفيره
        if epsg_code:
            try:
                import pyproj
                crs = pyproj.CRS.from_user_input(epsg_code)
                header.add_crs(crs)
            except Exception:
                pass

        las = laspy.LasData(header)
        las.x = coords[:, 0]
        las.y = coords[:, 1]
        las.z = coords[:, 2]
        las.classification = classifications.astype(np.uint8)

        if colors is not None:
            las.red = colors[:, 0].astype(np.uint16) << 8
            las.green = colors[:, 1].astype(np.uint16) << 8
            las.blue = colors[:, 2].astype(np.uint16) << 8

        # الكتابة التلقائية مع ضغط LAZ إذا انتهى المسار بـ .laz
        las.write(str(output_path))

    @classmethod
    def stream_large_file(
        cls, 
        file_path: Path, 
        chunk_size: int = 2_000_000
    ) -> Generator[np.ndarray, None, None]:
        """
        قارئ تدفقي (Streaming Generator) للسحب المليونية لمنع امتلاء الرام (OOM Crash).
        """
        with laspy.open(file_path) as reader:
            for chunk in reader.chunk_iterator(chunk_size):
                yield np.vstack((chunk.x, chunk.y, chunk.z)).T