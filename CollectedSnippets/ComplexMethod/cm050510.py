def parse_nomenclature_barcode(self, barcode):
        """ Attempts to interpret and parse a barcode.

        :param barcode:
        :type barcode: str
        :return: A object containing various information about the barcode, like as:

            - code: the barcode
            - type: the barcode's type
            - value: if the id encodes a numerical value, it will be put there
            - base_code: the barcode code with all the encoding parts set to
              zero; the one put on the product in the backend

        :rtype: dict
        """
        parsed_result = {
            'encoding': '',
            'type': 'error',
            'code': barcode,
            'base_code': barcode,
            'value': 0,
        }

        for rule in self.rule_ids:
            cur_barcode = barcode
            if rule.encoding == 'ean13' and check_barcode_encoding(barcode, 'upca') and self.upc_ean_conv in ['upc2ean', 'always']:
                cur_barcode = '0' + cur_barcode
            elif rule.encoding == 'upca' and check_barcode_encoding(barcode, 'ean13') and barcode[0] == '0' and self.upc_ean_conv in ['ean2upc', 'always']:
                cur_barcode = cur_barcode[1:]

            if not check_barcode_encoding(barcode, rule.encoding):
                continue

            match = self.match_pattern(cur_barcode, rule.pattern)
            if match['match']:
                if rule.type == 'alias':
                    barcode = rule.alias
                    parsed_result['code'] = barcode
                else:
                    parsed_result['encoding'] = rule.encoding
                    parsed_result['type'] = rule.type
                    parsed_result['value'] = match['value']
                    parsed_result['code'] = cur_barcode
                    if rule.encoding == "ean13":
                        parsed_result['base_code'] = self.sanitize_ean(match['base_code'])
                    elif rule.encoding == "upca":
                        parsed_result['base_code'] = self.sanitize_upc(match['base_code'])
                    else:
                        parsed_result['base_code'] = match['base_code']
                    return parsed_result

        return parsed_result