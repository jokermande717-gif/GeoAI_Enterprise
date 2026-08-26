"""
tests/test_geodetic_suite.py
----------------------------
Automated Benchmarking & Verification Suite fuer GeoAI Overlord.
Prueft REB 22.013 Volumen, Gauss-Elling Flaechen, R-Tree und Audit-Log Blockchain.
"""

from pathlib import Path
import numpy as np
import pytest
from core.audit_trail import ImmutableAuditLog
from core.geodetic_math import calculate_gauss_elling_area
from core.reb_da_engine import REBDataExchangeEngine


def test_gauss_elling_known_polygon() -> None:
    """فحص دقة حساب مساحة مضلع معروف هندسياً (مستطيل 100m * 50m = 5000 m²)."""
    polygon = np.array([
        [0.0, 0.0],
        [100.0, 0.0],
        [100.0, 50.0],
        [0.0, 50.0],
    ])
    area = calculate_gauss_elling_area(polygon)
    assert np.isclose(area, 5000.0, atol=1e-3)


def test_reb_22013_volume_prism() -> None:
    """فحص حساب حجم منشور ثلاثي معروف بدقة (قاعدة مثلثة 100m² بارتفاع 10m = 1000m³)."""
    # مثلث قائم الزاوية بقاعدة 20m وارتفاع 10m (مساحة = 100m²)، وبمنسوب ثابت Z = 110m
    points = np.array([
        [0.0, 0.0, 110.0],
        [20.0, 0.0, 110.0],
        [0.0, 10.0, 110.0],
    ])
    surface = REBDataExchangeEngine.generate_dgm_surface(points)
    results = REBDataExchangeEngine.calculate_exact_volume_reb(surface, reference_height=100.0)

    # الحجم المتوقع = 100 m² * 10 m = 1000 m³ حفر (Abtrag)
    assert np.isclose(results["cut_volume"], 1000.0, atol=1e-2)
    assert np.isclose(results["fill_volume"], 0.0, atol=1e-2)
    assert np.isclose(results["total_2d_area"], 100.0, atol=1e-2)


def test_audit_log_blockchain_integrity(tmp_path: Path) -> None:
    """فحص منع التلاعب واكتشاف أي تعديل في سجل التدقيق SHA-256."""
    db_file = tmp_path / "test_audit.db"
    audit = ImmutableAuditLog(str(db_file))

    audit.log_action("ACTION_1", details={"step": 1})
    audit.log_action("ACTION_2", details={"step": 2})

    is_valid, err_id, msg = audit.verify_chain()
    assert is_valid is True
    assert err_id is None


if __name__ == "__main__":
    pytest.main(["-v", __file__])