def _nemhandel_lookup_participant(self, edi_identification):
        """NAPTR DNS nemhandel participant lookup through Odoo's Nemhandel proxy"""
        if (edi_mode := self.env.company._get_nemhandel_edi_mode()) == 'demo':
            return

        sml_zone = f"edel.sml{'-demo' if edi_mode == 'test' else ''}.dataudveksling.dk"
        origin = self.env['account_edi_proxy_client.user']._get_proxy_urls()['nemhandel'][edi_mode]
        query = parse.urlencode({'peppol_identifier': edi_identification.lower(), 'zone': sml_zone})
        endpoint = f'{origin}/api/peppol/1/lookup?{query}'

        try:
            response = requests.get(endpoint, timeout=TIMEOUT)
        except requests.exceptions.RequestException as e:
            _logger.error("failed to query nemhandel participant %s: %s", edi_identification, e)
            return

        if not response.ok:
            _logger.info('unsuccessful response %s when querying nemhandel participant %s', response.status_code, edi_identification)
            return

        try:
            decoded_response = response.json()
        except ValueError:
            _logger.error('invalid JSON response %s when querying nemhandel participant %s', response.status_code, edi_identification)
            return

        if error := decoded_response.get('error'):
            if error.get('code') != 'NOT_FOUND':
                _logger.error('error when querying nemhandel participant %s: %s', edi_identification, error.get('message', 'unknown error'))
            return

        return decoded_response.get('result')