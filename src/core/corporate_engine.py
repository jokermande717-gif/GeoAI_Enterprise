import math

class CorporateEngine:
    """محرك المقايسات الآلية GAEB، التوجيه الآلي للحفارات، وكشف التعارضات التحت-أرضية"""
    
    @staticmethod
    def generate_gaeb_x83_tender(cut_m3, fill_m3, road_len_m):
        cost_cut = cut_m3 * 34.50
        cost_fill = fill_m3 * 29.00
        cost_road = road_len_m * 185.00
        total_eur = cost_cut + cost_fill + cost_road
        
        gaeb_xml = (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<GAEB xmlns="http://www.gaeb.de/GAEB_DA_XML/200407">\n'
            '  <GAEBInfo><Version>3.2</Version><Date>2026-08-26</Date></GAEBInfo>\n'
            '  <Award><DP><Title>Erdarbeiten und Trassierung VOB/C</Title>\n'
            '    <BoQ><ItemList>\n'
            f'      <Item><No>01.01.0010</No><Desc>Boden lösen und abtragen (BK 3-5)</Desc><Qty>{int(cut_m3)}</Qty><Unit>m3</Unit><Total>{cost_cut:,.2f}</Total></Item>\n'
            f'      <Item><No>01.01.0020</No><Desc>Planum herstellen und verdichten</Desc><Qty>{int(fill_m3)}</Qty><Unit>m3</Unit><Total>{cost_fill:,.2f}</Total></Item>\n'
            f'      <Item><No>01.02.0010</No><Desc>Frostschutzschicht Trasse</Desc><Qty>{int(road_len_m)}</Qty><Unit>m</Unit><Total>{cost_road:,.2f}</Total></Item>\n'
            '    </ItemList></BoQ>\n'
            '  </DP></Award>\n'
            '</GAEB>'
        )
        return {"gaeb_xml": gaeb_xml, "total_eur": total_eur}

    @staticmethod
    def check_subsurface_utility_clashes(buildings, utilities_depth=3.5):
        clashes = []
        for i, b in enumerate(buildings):
            b_depth = max(2.5, min(8.0, b.height * 0.12))
            if b_depth >= utilities_depth:
                clashes.append({
                    "bld_name": b.name,
                    "foundation_depth_m": b_depth,
                    "utility_type": "110kV Hochspannungskabel & Gasleitung",
                    "conflict": "KRITISCH (Konflikt bei -3.5m)"
                })
        return clashes
