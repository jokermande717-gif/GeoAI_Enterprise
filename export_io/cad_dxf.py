from pathlib import Path
from typing import Dict, Optional, Union
import ezdxf
import numpy as np
import pandas as pd


class CADExporter:
    """Enterprise CAD-Exporter mit GeoInfoDok NRW Layer-Standardisierung."""

    COLOR_GROUND: int = 3      # Grün (ALKIS / DGM Boden)
    COLOR_BUILDING: int = 1    # Rot (Gebäude)
    COLOR_VEGETATION: int = 2  # Gelb (Vegetation)
    COLOR_WATER: int = 5       # Blau (Gewässer)
    COLOR_DEFAULT: int = 7     # Weiß / Schwarz

    LAYER_MAPPING = {
        "boden": ("AX_StehendesGewaesser", COLOR_GROUND),
        "geb": ("AX_Gebaude", COLOR_BUILDING),
        "veg": ("AX_Bewuchs", COLOR_VEGETATION),
        "wasser": ("AX_Gewaesser", COLOR_WATER),
    }

    def __init__(self, dxf_version: str = "R2018") -> None:
        self.doc = ezdxf.new(dxfversion=dxf_version)
        self.msp = self.doc.modelspace()
        self._created_layers = set()

    def _ensure_layer(self, layer_name: str, color: int = COLOR_DEFAULT) -> str:
        clean_name = str(layer_name).strip().replace(" ", "_")
        if clean_name not in self._created_layers:
            if clean_name not in self.doc.layers:
                self.doc.layers.add(clean_name, color=color)
            self._created_layers.add(clean_name)
        return clean_name

    def export_dataframe_to_dxf(
        self,
        df: pd.DataFrame,
        output_path: Union[str, Path] = "vermessung.dxf",
        x_col: str = "x",
        y_col: str = "y",
        z_col: str = "z",
        layer_col: str = "Layer",
    ) -> Path:
        out_file = Path(output_path)
        out_file.parent.mkdir(parents=True, exist_ok=True)

        if df.empty:
            raise ValueError("Der übergebene DataFrame enthält keine Daten.")

        has_z = z_col in df.columns
        has_layer = layer_col in df.columns

        for _, row in df.iterrows():
            x = float(row[x_col])
            y = float(row[y_col])
            z = float(row[z_col]) if has_z else 0.0

            raw_layer = str(row[layer_col]) if has_layer else "VERM_PUNKTE"
            
            target_layer = "AX_Fortfuehrungsentscheid"
            color = self.COLOR_DEFAULT
            l_lower = raw_layer.lower()

            for key, (alkis_layer, alkis_color) in self.LAYER_MAPPING.items():
                if key in l_lower:
                    target_layer = alkis_layer
                    color = alkis_color
                    break

            layer_name = self._ensure_layer(target_layer, color=color)
            self.msp.add_point((x, y, z), dxfattribs={"layer": layer_name})

            if has_z:
                self.msp.add_text(
                    f"{z:.2f}",
                    dxfattribs={
                        "layer": f"{layer_name}_HOEHEN",
                        "height": 0.20,
                    },
                ).set_placement((x + 0.05, y + 0.05, z))

        self.doc.saveas(str(out_file))
        return out_file