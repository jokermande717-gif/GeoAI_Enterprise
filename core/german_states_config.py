# core/german_states_config.py
from dataclasses import dataclass
from typing import Dict

@dataclass
class GermanStateInfo:
    code: str
    name_de: str
    default_epsg: str
    center_lat: float
    center_lon: float
    road_authority: str

# بنية بيانات الولايات الألمانية الـ 16
GERMAN_STATES: Dict[str, GermanStateInfo] = {
    "DE-NW": GermanStateInfo("DE-NW", "Nordrhein-Westfalen", "EPSG:25832", 51.4818, 7.2162, "Landesbetrieb Straßenbau NRW"),
    "DE-BY": GermanStateInfo("DE-BY", "Bayern", "EPSG:25832", 48.7904, 11.4979, "Bayerische Straßenbauverwaltung"),
    "DE-BW": GermanStateInfo("DE-BW", "Baden-Württemberg", "EPSG:25832", 48.6616, 9.3501, "Regierungspräsidien Ba-Wü"),
    "DE-BE": GermanStateInfo("DE-BE", "Berlin", "EPSG:25833", 52.5200, 13.4050, "Senatsverwaltung für Mobilität Berlin"),
    "DE-BB": GermanStateInfo("DE-BB", "Brandenburg", "EPSG:25833", 52.4125, 12.5316, "Landesbetrieb Straßenwesen Brandenburg"),
    "DE-SN": GermanStateInfo("DE-SN", "Sachsen", "EPSG:25833", 51.0504, 13.7373, "Landesamt für Straßenbau und Verkehr Sachsen"),
    "DE-NI": GermanStateInfo("DE-NI", "Niedersachsen", "EPSG:25832", 52.6367, 9.8451, "NLStBV Niedersachsen"),
    "DE-HE": GermanStateInfo("DE-HE", "Hessen", "EPSG:25832", 50.6521, 9.1624, "Hessen Mobil"),
    "DE-RP": GermanStateInfo("DE-RP", "Rheinland-Pfalz", "EPSG:25832", 49.9139, 7.4539, "Landesbetrieb Mobilität RLP"),
    "DE-SH": GermanStateInfo("DE-SH", "Schleswig-Holstein", "EPSG:25832", 54.2194, 9.6961, "LBV.SH"),
    "DE-TH": GermanStateInfo("DE-TH", "Thüringen", "EPSG:25832", 50.8848, 11.0805, "TLBV Thüringen"),
    "DE-ST": GermanStateInfo("DE-ST", "Sachsen-Anhalt", "EPSG:25832", 51.9503, 11.6923, "Landesstraßenbaubehörde Sachsen-Anhalt"),
    "DE-MV": GermanStateInfo("DE-MV", "Mecklenburg-Vorpommern", "EPSG:25833", 53.6127, 12.4296, "Straßenbauverwaltung M-V"),
    "DE-SL": GermanStateInfo("DE-SL", "Saarland", "EPSG:25832", 49.3964, 7.0230, "Landesbetrieb für Straßenbau Saarland"),
    "DE-HB": GermanStateInfo("DE-HB", "Bremen", "EPSG:25832", 53.0793, 8.8017, "Amt für Straßen und Verkehr Bremen"),
    "DE-HH": GermanStateInfo("DE-HH", "Hamburg", "EPSG:25832", 53.5511, 9.9937, "Landesbetrieb Straßen, Brücken und Gewässer Hamburg")
}

# خدمة الخرائط الموحدة لجميع أنحاء ألمانيا (BKG / basemap.de)
GERMANY_FEDERAL_WMS = {
    "url": "https://sgx.geodatenzentrum.de/wms_basemapde",
    "layer": "de_basemapde_web_raster_farbe",
    "attribution": "© GeoBasis-DE / BKG"
}