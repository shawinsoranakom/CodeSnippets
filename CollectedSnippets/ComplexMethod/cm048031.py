def _get_address_node(self, vals):
        """ Generic helper to generate the Address node for a res.partner or res.bank. """
        if 'consolidated_invoice' not in vals:
            return super()._get_address_node(vals)

        partner = vals['partner']
        country_key = 'country' if partner._name == 'res.bank' else 'country_id'
        state_key = 'state' if partner._name == 'res.bank' else 'state_id'
        country = partner[country_key]
        state = partner[state_key]

        subentity_code = partner.state_id.code or ''
        # The API does not expect the country code inside the state code, only the number part.
        if f'{partner.country_id.code}-' in subentity_code:
            subentity_code = subentity_code.split('-')[1]

        return {
            'cac:AddressLine': [
                {'cbc:Line': {'_text': partner.street or None}},
                {'cbc:Line': {'_text': partner.street2 or None}},
            ],
            'cbc:CityName': {'_text': partner.city},
            'cbc:PostalZone': {'_text': partner.zip},
            'cbc:CountrySubentity': {'_text': state.name},
            'cbc:CountrySubentityCode': {'_text': subentity_code},
            'cac:Country': {
                'cbc:IdentificationCode': {
                    'listID': 'ISO3166-1',
                    'listAgencyID': '6',
                    '_text': COUNTRY_CODE_MAP.get(country.code),
                },
                'cbc:Name': {'_text': country.name},
            },
        }