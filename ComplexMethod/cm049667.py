def _perform_complete_place_search(self, address, api_key=None, google_place_id=None, language_code=None, session_id=None):
        params = {
            'key': api_key,
            'place_id': google_place_id,
            'fields': 'address_component,adr_address'
        }

        if language_code:
            params['language'] = language_code
        if session_id:
            params['sessiontoken'] = session_id

        try:
            results = self._call_google_route("/details/json", params)
        except (TimeoutError, ValueError) as e:
            _logger.error(e)
            return {'address': None}

        if results.get('error_message'):
            _logger.error(results['error_message'])

        try:
            html_address = results['result']['adr_address']
            results = results['result']['address_components']  # Get rid of useless extra data
        except KeyError:
            return {'address': None}

        # Keep only the first known type from the list of types
        for res in results:
            types = res.pop('types')
            res['type'] = next(filter(FIELDS_MAPPING.get, types), types[0])

        # Sort the result by their priority.
        results.sort(key=lambda r: FIELDS_PRIORITY.index(r['type']) if r['type'] in FIELDS_PRIORITY else 100)

        standard_address = self._translate_google_to_standard(results)

        if 'number' not in standard_address:
            standard_address['number'] = self._guess_number_from_input(address, standard_address)
            standard_address['formatted_street_number'] = f'{standard_address["number"]} {standard_address.get("street", "")}'.strip()
        else:
            formatted_from_html = html2plaintext(html_address.split(',')[0])
            formatted_manually = f'{standard_address["number"]} {standard_address.get("street", "")}'.strip()
            # Sometimes, the google api sends back abbreviated data :
            # "52 High Road Street" becomes "52 HR St" for example. We usually take the result from google, but if it's an abbreviation, take our guess instead.
            if len(formatted_from_html) >= len(formatted_manually):
                standard_address['formatted_street_number'] = formatted_from_html
            else:
                standard_address['formatted_street_number'] = formatted_manually
        return standard_address