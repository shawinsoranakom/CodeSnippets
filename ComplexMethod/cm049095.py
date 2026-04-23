def compute_p_12(tag_names):
            """
                Determines the KSeF tax rate code (P_12) based on the line's tax.
                Prioritizes tax amount for standard rates, and Tags/Names for special 0% cases.
                Mapping was determined by looking at the Tax Report lines.
            """
            # "0 WDT": Intra-Community supply of goods (K_21)
            if 'K_21' in tag_names:
                return "0 WDT"
            # "0 EX": Export of goods in case of 0% rate for export of goods (K_22)
            if 'K_22' in tag_names:
                return "0 EX"
            # "oo": Supply of goods, taxable person acquiring (K_31)
            if 'K_31' in tag_names:
                return "oo"
            # Services included in art. 100.1.4 (K_12)
            if 'K_12' in tag_names:
                return "np II"
            # Supply of goods/services, out of the country (K_11, OSS)
            if 'K_11' in tag_names or any('OSS' in tag for tag in tag_names):
                return "np I"
            # "zw": Supply of goods/services, domestic, exempt (K_10) - must fill P_19
            if 'K_10' in tag_names:
                return "zw"
            # "0 KR": Supply of goods/services, domestic, 0% (K_13)
            if 'K_13' in tag_names:
                return "0 KR"
            # "23": Supply of goods/services, domestic, 23% (K_19)
            if 'K_19' in tag_names:
                return "23"
            # "8": Supply of goods/services, domestic, 8% (K_17)
            if 'K_17' in tag_names:
                return "8"
            # "5": Supply of goods/services, domestic, 5% (K_15)
            if 'K_15' in tag_names:
                return "5"
            # No tax? It's exempt
            return "zw"