def _get_party_node(self, vals):
        partner = vals['partner']
        commercial_partner = partner.commercial_partner_id
        is_customer = vals['role'] == 'customer'
        return {
            'cac:PartyIdentification': {
                'cbc:ID': {'_text': commercial_partner.vat, 'schemeID': 'TN' if partner.country_code == 'JO' else 'PN'},
            } if not vals['is_refund'] and is_customer else None,
            'cac:PostalAddress': self._get_address_node(vals),
            'cac:PartyTaxScheme': {
                'cbc:CompanyID': {'_text': commercial_partner.vat} if not vals['is_refund'] or not is_customer else None,
                'cac:TaxScheme': {
                    'cbc:ID': {'_text': 'VAT'}
                },
            },
            'cac:PartyLegalEntity': {
                'cbc:RegistrationName': {'_text': commercial_partner.name},
            } if not vals['is_refund'] or not is_customer else None,
        }