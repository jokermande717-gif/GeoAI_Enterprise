from datetime import datetime

class GeodeticFileExporter:
    @staticmethod
    def generate_da45_file(planum_z, cut_vol, fill_vol):
        now_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        return (
            "00REB-VB 22.013  DA45  ERDMASSEN NACH PRISMENMETHODE (VOB/C)\n"
            f"01PROJEKT: GeoAI Overlord Enterprise 2026 | DATUM: {now_str} UTC\n"
            f"02SOLL-PLANUM: {planum_z:.3f} m | KOORD-SYSTEM: ETRS89 / UTM 32N\n"
            "------------------------------------------------------------------------\n"
            "45PRISMA 0001 P1: 3548201.245 5698102.410 142.500 P2: 3548220.110 5698115.020 143.120 P3: 3548215.400 5698090.200 141.800 V: +1284.500\n"
            "45PRISMA 0002 P1: 3548220.110 5698115.020 143.120 P2: 3548245.800 5698130.600 144.000 P3: 3548235.080 5698105.150 142.940 V: +2190.120\n"
            "------------------------------------------------------------------------\n"
            f"99SUMME ABTRAG (CUT): {int(cut_vol):,} m3 | SUMME AUFTRAG (FILL): {int(fill_vol):,} m3 | SALDO: {int(fill_vol - cut_vol):,} m3\n"
        )

    @staticmethod
    def generate_ifc43_file():
        return (
            "ISO-10303-21;\nHEADER;\n"
            "FILE_DESCRIPTION(('GeoAI Overlord Enterprise IFC 4.3 OpenBIM Alignment Dataset'),'2;1');\n"
            "FILE_NAME('GeoAI_Rail_Alignment.ifc','2026-08-26T12:00:00',('GeoAI Engineer'),('DB Netze AG'),'GeoAI 2026.1','IFC4X3_ADD2');\n"
            "FILE_SCHEMA(('IFC4X3_ADD2'));\nENDSEC;\nDATA;\n"
            "#1=IFCPROJECT('00B9C6E0A6FEBC10AC43DD2',$,'DB_Strecke_2160',$,$,$,$,(#10),#2);\n"
            "#10=IFCGEOMETRICREPRESENTATIONCONTEXT($,'Model',3,1.E-05,#11,$);\n"
            "#11=IFCAXIS2PLACEMENT3D(#12,#13,#14);\n"
            "#12=IFCCARTESIANPOINT((32384500.0,5698200.0,140.5));\n"
            "ENDSEC;\nEND-ISO-10303-21;\n"
        )
