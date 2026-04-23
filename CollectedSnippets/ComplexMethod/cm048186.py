def autocomplete_by_vat(self, vat, query_country_id, timeout=15):
        query_country_id = query_country_id or self.env.company.country_id.id
        query_country_code = self.env['res.country'].browse(query_country_id).code
        response, _ = self.env['iap.autocomplete.api']._request_partner_autocomplete('search_by_vat', {
            'query': vat,
            'query_country_code': query_country_code,
        }, timeout=timeout)
        if response and not response.get("error"):
            results = []
            for suggestion in response.get("data"):
                results.append(self._format_data_company(suggestion))
            return results
        else:
            vies_result = None
            try:
                vies_result = check_vies(vat, timeout=timeout)
            except Exception:
                _logger.warning("Failed VIES VAT check.", exc_info=True)
            if vies_result:
                name = vies_result['name']
                if vies_result['valid'] and name != '---':
                    address = list(filter(bool, vies_result['address'].split('\n')))
                    street = address[0]
                    zip_city_record = next(filter(lambda addr: re.match(r'^\d.*', addr), address[1:]), None)
                    zip_city = zip_city_record.split(' ', 1) if zip_city_record else [None, None]
                    street2 = next((addr for addr in filter(lambda addr: addr != zip_city_record, address[1:])), None)
                    return [self._iap_replace_location_codes({
                        'name': name,
                        'vat': vat,
                        'street': street,
                        'street2': street2,
                        'city': zip_city[1],
                        'zip': zip_city[0],
                        'country_code': vies_result['countryCode'],
                    })]
            return []