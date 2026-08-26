import math
from pathlib import Path
from typing import Any, Dict, Optional, Tuple
from lxml import etree


def calculate_klothoide_parameters(
    L: float, R: float, A: Optional[float] = None
) -> Dict[str, float]:
    """Berechnet die exakten geometrischen Parameter einer Klothoide (Übergangsbogen).

    Verwendet Taylor-Reihenentwicklungen hoher Ordnung für die Fresnel-Integrale
    gemäß den Richtlinien für die Anlage von Straßen (RAS-L / RAA).

    Beziehung: A² = R * L
    """
    if L <= 0:
        raise ValueError("Die Klothoidenlänge L muss größer als 0 sein.")

    if A is None:
        if R <= 0:
            raise ValueError("Radius R muss positiv sein, wenn A nicht angegeben ist.")
        A = math.sqrt(R * L)
    else:
        if R <= 0:
            R = (A * A) / L

    tau_rad = L / (2.0 * R)
    tau_gon = tau_rad * (200.0 / math.pi)

    A2 = A * A
    A4 = A2 * A2
    A8 = A4 * A4
    A12 = A8 * A4

    L3 = L * L * L
    L5 = L3 * L * L
    L7 = L5 * L * L
    L9 = L7 * L * L
    L11 = L9 * L * L
    L13 = L11 * L * L

    X = L - (L5 / (40.0 * A4)) + (L9 / (3456.0 * A8)) - (L13 / (599040.0 * A12))

    A6 = A4 * A2
    A10 = A8 * A2

    Y = (L3 / (6.0 * A2)) - (L7 / (336.0 * A6)) + (L11 / (42240.0 * A10))

    delta_R = Y - R * (1.0 - math.cos(tau_rad))
    X_m = X - R * math.sin(tau_rad)

    return {
        "A": float(A),
        "L": float(L),
        "R": float(R),
        "tau_rad": float(tau_rad),
        "tau_gon": float(tau_gon),
        "X": float(X),
        "Y": float(Y),
        "delta_R": float(delta_R),
        "X_m": float(X_m),
    }


class LandXMLParser:
    """Enterprise-LandXML Parser zur Extraktion von Trassierungsachsen, Querprofilen und DGM-Oberflächen."""

    def __init__(self, xml_path: str | Path) -> None:
        self.xml_path = Path(xml_path)
        if not self.xml_path.exists():
            raise FileNotFoundError(f"LandXML Datei nicht gefunden: {self.xml_path}")

        self.tree: Optional[etree._ElementTree] = None
        self.root: Optional[etree._Element] = None
        self.namespaces: Dict[str, str] = {}
        self._load_file()

    def _load_file(self) -> None:
        parser = etree.XMLParser(remove_blank_text=True, recover=True)
        self.tree = etree.parse(str(self.xml_path), parser)
        self.root = self.tree.getroot()

        if self.root.tag.startswith("{"):
            ns_url = self.root.tag.split("}")[0].strip("{")
            self.namespaces = {"lxml": ns_url}

    def parse_alignments(self) -> List[Dict[str, Any]]:
        alignments = []
        ns = self.namespaces
        xpath_expr = "//lxml:Alignment" if ns else "//Alignment"

        alignment_nodes = self.root.xpath(xpath_expr, namespaces=ns)

        for align_node in alignment_nodes:
            align_data = {
                "name": align_node.get("name", "Unbenannte Achse"),
                "length": float(align_node.get("length", 0.0)),
                "start_station": float(align_node.get("staStart", 0.0)),
                "elements": [],
                "coord_geom": [],
            }

            geom_xpath = ".//lxml:CoordGeom/*" if ns else ".//CoordGeom/*"
            geom_nodes = align_node.xpath(geom_xpath, namespaces=ns)

            for g_node in geom_nodes:
                elem_type = etree.QName(g_node.tag).localname
                start_pt_node = g_node.find("lxml:Start" if ns else "Start", namespaces=ns)
                end_pt_node = g_node.find("lxml:End" if ns else "End", namespaces=ns)

                start_pt = None
                end_pt = None

                if start_pt_node is not None and start_pt_node.text:
                    coords = [float(c) for c in start_pt_node.text.strip().split()]
                    start_pt = tuple(coords)

                if end_pt_node is not None and end_pt_node.text:
                    coords = [float(c) for c in end_pt_node.text.strip().split()]
                    end_pt = tuple(coords)

                elem_info = {
                    "type": elem_type,
                    "start_point": start_pt,
                    "end_point": end_pt,
                    "length": float(g_node.get("length", 0.0)),
                    "radius": float(g_node.get("radius", 0.0)) if g_node.get("radius") else None,
                    "spiral_type": g_node.get("spiType") if g_node.get("spiType") else None,
                }
                align_data["coord_geom"].append(elem_info)

            alignments.append(align_data)

        return alignments

    def parse_cross_sections(self) -> List[Dict[str, Any]]:
        cross_sections = []
        ns = self.namespaces
        xpath_expr = "//lxml:CrossSect" if ns else "//CrossSect"

        cs_nodes = self.root.xpath(xpath_expr, namespaces=ns)

        for cs_node in cs_nodes:
            station = float(cs_node.get("sta", 0.0))
            cs_data = {
                "station": station,
                "name": cs_node.get("name", f"Station_{station:.2f}"),
                "surfaces": [],
            }

            surf_xpath = ".//lxml:CrossSectSurf" if ns else ".//CrossSectSurf"
            surf_nodes = cs_node.xpath(surf_xpath, namespaces=ns)

            for s_node in surf_nodes:
                surf_name = s_node.get("name", "Gelaende")
                points_node = s_node.find("lxml:PntList" if ns else "PntList", namespaces=ns)

                points = []
                if points_node is not None and points_node.text:
                    raw_coords = points_node.text.strip().split()
                    for i in range(0, len(raw_coords), 2):
                        if i + 1 < len(raw_coords):
                            offset = float(raw_coords[i])
                            elevation = float(raw_coords[i + 1])
                            points.append((offset, elevation))

                cs_data["surfaces"].append({
                    "surface_name": surf_name,
                    "points": points,
                })

            cross_sections.append(cs_data)

        return cross_sections