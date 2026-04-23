def _get_party_node(self, vals):
        partner = vals['partner']
        role = vals['role']
        commercial_partner = partner.commercial_partner_id

        party_node = {}

        if identification_number := self._get_partner_party_identification_number(commercial_partner):
            party_node['cac:PartyIdentification'] = {
                'cbc:ID': {
                    '_text': identification_number,
                    'schemeID': commercial_partner.l10n_sa_edi_additional_identification_scheme,
                }
            }

        party_node.update({
            'cac:PartyName': {
                'cbc:Name': {'_text': partner.display_name}
            },
            'cac:PostalAddress': self._get_address_node(vals),
            'cac:PartyTaxScheme': {
                'cbc:RegistrationName': {'_text': commercial_partner.name},
                'cbc:CompanyID': {'_text': commercial_partner.vat},
                'cac:RegistrationAddress': self._get_address_node({'partner': commercial_partner}),
                'cac:TaxScheme': {
                    'cbc:ID': {'_text': 'VAT'}
                }
            } if (role != 'customer' or partner.country_id.code == 'SA') and commercial_partner.vat and commercial_partner.vat != '/' else None,  # BR-KSA-46
            'cac:PartyLegalEntity': {
                'cbc:RegistrationName': {'_text': commercial_partner.name},
                'cbc:CompanyID': {'_text': commercial_partner.vat} if commercial_partner.country_code == 'SA' else None,
                'cac:RegistrationAddress': self._get_address_node({'partner': commercial_partner}),
            },
            'cac:Contact': {
                'cbc:ID': {'_text': partner.id},
                'cbc:Name': {'_text': partner.name},
                'cbc:Telephone': {
                    '_text': re.sub(r"[^+\d]", '', partner.phone) if partner.phone else None
                },
                'cbc:ElectronicMail': {'_text': partner.email},
            }
        })
        return party_node