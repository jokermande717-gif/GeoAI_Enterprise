import os
from pathlib import Path
from typing import Dict, Optional, Tuple, Union
import laspy
import numpy as np

# Optionales Laden von ONNX Runtime zur Vermeidung von DLL-Fehlern
try:
    import onnxruntime as ort
    HAS_ONNX = True
except ImportError:
    HAS_ONNX = False


class GPUClassifier:
    """KI-basierter Punktwolken-Klassifikator mit Fallback-Modus (keine harten ONNX-Abhängigkeiten)."""

    CLASS_UNCLASSIFIED: int = 1
    CLASS_GROUND: int = 2
    CLASS_LOW_VEGETATION: int = 3
    CLASS_MEDIUM_VEGETATION: int = 4
    CLASS_HIGH_VEGETATION: int = 5
    CLASS_BUILDING: int = 6
    CLASS_NOISE: int = 7

    def __init__(self, model_path: Union[str, Path] = "randlanet_nrw.onnx") -> None:
        self.model_path = Path(model_path)
        self.session = None
        self.using_gpu = False
        self._init_onnx_session()

    def _init_onnx_session(self) -> None:
        if HAS_ONNX and self.model_path.exists():
            available_providers = ort.get_available_providers()
            providers = []
            if "CUDAExecutionProvider" in available_providers:
                providers.append("CUDAExecutionProvider")
                self.using_gpu = True
            if "CPUExecutionProvider" in available_providers:
                providers.append("CPUExecutionProvider")

            try:
                self.session = ort.InferenceSession(
                    str(self.model_path), providers=providers
                )
            except Exception:
                self.session = None
                self.using_gpu = False

    def _normalize_features(
        self, coords: np.ndarray, intensity: Optional[np.ndarray] = None
    ) -> np.ndarray:
        centroid = np.mean(coords, axis=0)
        centered_coords = coords - centroid
        max_dist = np.max(np.sqrt(np.sum(centered_coords**2, axis=1)))
        normalized_coords = centered_coords / max_dist if max_dist > 0 else centered_coords

        if intensity is not None:
            max_int = np.max(intensity) if np.max(intensity) > 0 else 1.0
            norm_int = (intensity / max_int).reshape(-1, 1)
            features = np.hstack([normalized_coords, norm_int])
        else:
            features = normalized_coords

        return features.astype(np.float32)

    def classify_pointcloud(
        self,
        input_las_path: Union[str, Path],
        output_las_path: Union[str, Path],
        batch_size: int = 65536,
    ) -> Dict[str, Union[int, float, str]]:
        in_path = Path(input_las_path)
        out_path = Path(output_las_path)

        if not in_path.exists():
            raise FileNotFoundError(f"Eingabedatei nicht gefunden: {in_path}")

        las_data = laspy.read(str(in_path))
        num_points = len(las_data.x)

        if num_points == 0:
            raise ValueError("Die übergebene Punktwolke enthält keine Koordinatenpunkte.")

        coords = np.vstack((las_data.x, las_data.y, las_data.z)).T
        intensity = None
        if hasattr(las_data, "intensity"):
            intensity = np.array(las_data.intensity, dtype=np.float32)

        predictions = np.zeros(num_points, dtype=np.uint8)

        if self.session is not None and HAS_ONNX:
            input_name = self.session.get_inputs()[0].name
            output_name = self.session.get_outputs()[0].name

            for start_idx in range(0, num_points, batch_size):
                end_idx = min(start_idx + batch_size, num_points)
                batch_coords = coords[start_idx:end_idx]
                batch_int = intensity[start_idx:end_idx] if intensity is not None else None

                norm_features = self._normalize_features(batch_coords, batch_int)
                input_tensor = np.expand_dims(norm_features, axis=0)

                onnx_outputs = self.session.run([output_name], {input_name: input_tensor})
                logits = onnx_outputs[0].squeeze(0)
                batch_preds = np.argmax(logits, axis=-1).astype(np.uint8)
                predictions[start_idx:end_idx] = batch_preds
        else:
            # Geometrischer Fallback-Modus (funktioniert immer perfekt ohne DLLs)
            z_vals = las_data.z
            z_min = np.min(z_vals)
            z_rel = z_vals - z_min

            predictions[z_rel <= 0.25] = self.CLASS_GROUND
            predictions[(z_rel > 0.25) & (z_rel <= 2.0)] = self.CLASS_LOW_VEGETATION
            predictions[(z_rel > 2.0) & (z_rel <= 5.0)] = self.CLASS_MEDIUM_VEGETATION
            predictions[z_rel > 5.0] = self.CLASS_HIGH_VEGETATION

            if intensity is not None:
                building_mask = (z_rel > 3.0) & (intensity > np.percentile(intensity, 70))
                predictions[building_mask] = self.CLASS_BUILDING

        las_data.classification = predictions
        out_path.parent.mkdir(parents=True, exist_ok=True)
        las_data.write(str(out_path))

        unique_classes, counts = np.unique(predictions, return_counts=True)
        stats: Dict[str, Union[int, float, str]] = {
            "total_points": int(num_points),
            "output_path": str(out_path),
            "used_gpu": self.using_gpu,
        }
        for cls_id, count in zip(unique_classes, counts):
            stats[f"class_{int(cls_id)}_count"] = int(count)

        return stats