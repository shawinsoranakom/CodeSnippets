def _process_enriched_response(self, response, error):
        if response and response.get('data'):
            result = self._format_data_company(response.get('data'))
        else:
            result = {}

        if response and response.get('credit_error'):
            result.update({
                'error': True,
                'error_message': 'Insufficient Credit'
            })
        elif response and response.get('error'):
            result.update({
                'error': True,
                'error_message': _('Unable to enrich company (no credit was consumed).'),
            })
        elif error:
            result.update({
                'error': True,
                'error_message': error
            })
        return self._validate_partner_autocomplete_response(result)