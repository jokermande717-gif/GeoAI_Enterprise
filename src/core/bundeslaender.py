class BundeslaenderEngine:
    """16 German Federal States Spatial Metadata & Local CRS Grids"""
    STATES = {
        "NRW": {"name": "Nordrhein-Westfalen", "lat": 51.2277, "lon": 6.7735, "zoom": 11, "crs": "ETRS89 / UTM 32N", "epsg": 25832, "grid": "BeTA2007_NRW"},
        "BY":  {"name": "Bayern", "lat": 48.1351, "lon": 11.5820, "zoom": 11, "crs": "ETRS89 / UTM 32N", "epsg": 25832, "grid": "BY_NTv2_2007"},
        "BW":  {"name": "Baden-Württemberg", "lat": 48.7758, "lon": 9.1829, "zoom": 11, "crs": "ETRS89 / UTM 32N", "epsg": 25832, "grid": "BW_NTv2"},
        "HE":  {"name": "Hessen", "lat": 50.1109, "lon": 8.6821, "zoom": 11, "crs": "ETRS89 / UTM 32N", "epsg": 25832, "grid": "HeTa2010"},
        "BE":  {"name": "Berlin", "lat": 52.5200, "lon": 13.4050, "zoom": 12, "crs": "ETRS89 / UTM 33N", "epsg": 25833, "grid": "BER_Soldner_2007"},
        "SN":  {"name": "Sachsen", "lat": 51.0504, "lon": 13.7373, "zoom": 11, "crs": "ETRS89 / UTM 33N", "epsg": 25833, "grid": "SN_NTv2"},
        "NI":  {"name": "Niedersachsen", "lat": 52.3759, "lon": 9.7320, "zoom": 11, "crs": "ETRS89 / UTM 32N", "epsg": 25832, "grid": "BeTA2007_NI"},
        "RP":  {"name": "Rheinland-Pfalz", "lat": 49.9929, "lon": 8.2473, "zoom": 11, "crs": "ETRS89 / UTM 32N", "epsg": 25832, "grid": "RP_NTv2"},
        "SH":  {"name": "Schleswig-Holstein", "lat": 54.3233, "lon": 10.1228, "zoom": 11, "crs": "ETRS89 / UTM 32N", "epsg": 25832, "grid": "SH_NTv2"},
        "TH":  {"name": "Thüringen", "lat": 50.9848, "lon": 11.0299, "zoom": 11, "crs": "ETRS89 / UTM 32N", "epsg": 25832, "grid": "TH_NTv2"},
        "ST":  {"name": "Sachsen-Anhalt", "lat": 52.1205, "lon": 11.6276, "zoom": 11, "crs": "ETRS89 / UTM 32N", "epsg": 25832, "grid": "ST_NTv2"},
        "MV":  {"name": "Mecklenburg-Vorpommern", "lat": 53.6355, "lon": 11.4012, "zoom": 11, "crs": "ETRS89 / UTM 33N", "epsg": 25833, "grid": "MV_NTv2"},
        "BB":  {"name": "Brandenburg", "lat": 52.3906, "lon": 13.0645, "zoom": 11, "crs": "ETRS89 / UTM 33N", "epsg": 25833, "grid": "BB_NTv2"},
        "HH":  {"name": "Hamburg", "lat": 53.5511, "lon": 9.9937, "zoom": 12, "crs": "ETRS89 / UTM 32N", "epsg": 25832, "grid": "HH_NTv2"},
        "SL":  {"name": "Saarland", "lat": 49.2402, "lon": 6.9969, "zoom": 11, "crs": "ETRS89 / UTM 32N", "epsg": 25832, "grid": "SL_NTv2"},
        "HB":  {"name": "Bremen", "lat": 53.0793, "lon": 8.8017, "zoom": 12, "crs": "ETRS89 / UTM 32N", "epsg": 25832, "grid": "HB_NTv2"}
    }

    @classmethod
    def get_state(cls, code):
        return cls.STATES.get(code, cls.STATES["NRW"])
