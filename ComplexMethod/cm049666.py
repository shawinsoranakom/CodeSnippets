def _perform_place_search(self, partial_address, api_key=None, session_id=None, language_code=None, country_code=None):
        minimal_input_size = int(request.env['ir.config_parameter'].sudo().get_param('google_address_autocomplete.minimal_partial_address_size', '5'))
        if len(partial_address) <= minimal_input_size:
            return {
                'results': [],
                'session_id': session_id
            }

        params = {
            'key': api_key,
            'fields': 'formatted_address,name',
            'inputtype': 'textquery',
            'types': 'address',
            'input': partial_address
        }
        if country_code:
            params['components'] = f'country:{country_code}'
        if language_code:
            params['language'] = language_code
        if session_id:
            params['sessiontoken'] = session_id

        try:
            results = self._call_google_route("/autocomplete/json", params)
        except (TimeoutError, ValueError) as e:
            _logger.error(e)
            return {
                'results': [],
                'session_id': session_id
            }

        if results.get('error_message'):
            _logger.error(results['error_message'])

        results = results.get('predictions', [])

        # Convert google specific format to standard format.
        return {
            'results': [{
                'formatted_address': result['description'],
                'google_place_id': result['place_id'],
            } for result in results],
            'session_id': session_id
        }