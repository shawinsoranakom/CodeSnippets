def _get_party_node(self, vals):
        # EXTENDS account.edi.xml.ubl_20
        party_node = super()._get_party_node(vals)
        partner = vals['partner'].commercial_partner_id
        vat = format_vat_number(partner, partner.vat)
        cvr = format_vat_number(partner, partner.company_registry) or vat
        party_node['cac:PartyLegalEntity'].update({
            # Even if not enforced by Schematron, only CVR (CPR which we don't use) can be used
            # https://oioubl21.oioubl.dk/Classes/da/PartyLegalEntity.html
            'cbc:CompanyID': {
                '_text': cvr,
                'schemeID': 'DK:CVR' if vat[:2] == 'DK' else 'ZZZ'
            },
        })
        if vat and vat != '/':
            party_node['cac:PartyTaxScheme'].update({
                # Only DK:SE for PartyTaxScheme https://oioubl21.oioubl.dk/Classes/da/PartyTaxScheme.html
                'cbc:CompanyID': {
                    '_text': vat,
                    'schemeID': 'DK:SE' if vat[:2] == 'DK' else 'ZZZ'
                },
                'cac:TaxScheme': {
                    'cbc:ID': {
                        '_text': 63,
                        'schemeID': 'urn:oioubl:id:taxschemeid-1.5',
                    },
                    'cbc:Name': {'_text': 'Moms'},
                },
            })
        if partner.nemhandel_identifier_type and partner.nemhandel_identifier_value:
            prefix = 'DK' if partner.nemhandel_identifier_type in {'0184', '0198'} else ''
            party_node['cbc:EndpointID'] = {
                '_text': f'{prefix}{partner.nemhandel_identifier_value}',
                'schemeID': SCHEME_ID_MAPPING[partner.nemhandel_identifier_type],
            }
        if partner.nemhandel_identifier_value or partner.ref:
            prefix = 'DK' if partner.nemhandel_identifier_type in {'0184', '0198'} else ''
            party_node['cac:PartyIdentification'] = {
                'cbc:ID': {
                    '_text': f'{prefix}{partner.nemhandel_identifier_value or partner.ref}',
                    'schemeID': SCHEME_ID_MAPPING[partner.nemhandel_identifier_type],
                }
            }

        return party_node