def _get_party_node(self, vals):
        partner = vals['partner']
        commercial_partner = partner.commercial_partner_id
        vat = format_vat_number(commercial_partner)

        if partner.peppol_endpoint and partner.peppol_eas in EAS_SCHEME_ID_MAPPING:
            # if we don't know the mapping with real names for the Peppol Endpoint, fallback on VAT simply
            endpoint_id = partner.peppol_endpoint
            scheme_id = EAS_SCHEME_ID_MAPPING[partner.peppol_eas]
            if (scheme_id in ('DK:CVR', 'FR:SIRET') or scheme_id[3:] == 'VAT') and endpoint_id.isnumeric():
                endpoint_id = scheme_id[:2] + endpoint_id
        else:
            endpoint_id = format_vat_number(partner)
            country_code = endpoint_id[:2]
            match country_code:
                case 'DK':
                    scheme_id = 'DK:CVR'
                case 'FR':
                    scheme_id = 'FR:SIRET'
                    # SIRET is the french company registry
                    endpoint_id = (partner.company_registry or "").replace(" ", "")
                case _:
                    scheme_id = f'{country_code}:VAT'

        return {
            'cbc:EndpointID': {
                # list of possible endpointID available at
                # https://www.oioubl.info/documents/en/en/Guidelines/OIOUBL_GUIDE_ENDPOINT.pdf
                '_text': endpoint_id,
                'schemeID': scheme_id,
            },
            'cbc:IndustryClassificationCode': None,
            'cac:PartyIdentification': [
                {
                    'cbc:ID': {
                        '_text': party_vals.get('id'),
                        'schemeName': party_vals.get('id_attrs', {}).get('schemeName'),
                        'schemeID': party_vals.get('id_attrs', {}).get('schemeID'),
                    }
                }
                for party_vals in vals.get('party_identification_vals', [])
            ],
            'cac:PartyName': {
                'cbc:Name': {'_text': partner.display_name}
            },
            'cac:PostalAddress': self._get_address_node(vals),
            'cac:PartyTaxScheme': {
                'cbc:RegistrationName': {'_text': commercial_partner.name},
                'cbc:CompanyID': {
                    '_text': vat,
                    # SE is the danish vat number
                    # DK:SE indicates we're using it and 'ZZZ' is for international number
                    # https://www.oioubl.info/Codelists/en/urn_oioubl_scheme_partytaxschemecompanyid-1.1.html
                    'schemeID': 'DK:SE' if vat[:2] == 'DK' else 'ZZZ',
                },
                'cac:RegistrationAddress': self._get_address_node({'partner': commercial_partner}),
                'cac:TaxScheme': {
                    # [BR-CO-09] if the PartyTaxScheme/TaxScheme/ID == 'VAT', CompanyID must start with a country code prefix.
                    # In some countries however, the CompanyID can be with or without country code prefix and still be perfectly
                    # valid (RO, HU, non-EU countries).
                    # We have to handle their cases by changing the TaxScheme/ID to 'something other than VAT',
                    # preventing the trigger of the rule.
                    'cbc:ID': {
                        '_text': 'VAT',
                        # the doc says it could be empty but the schematron says otherwise
                        # https://www.oioubl.info/Classes/en/TaxScheme.html
                        'schemeID': 'urn:oioubl:id:taxschemeid-1.5',
                    },
                    'cbc:Name': {'_text': 'VAT'},
                },
            },
            'cac:PartyLegalEntity': {
                'cbc:RegistrationName': {'_text': commercial_partner.name},
                'cbc:CompanyID': {
                    '_text': vat,
                    'schemeID': 'DK:CVR' if vat[:2] == 'DK' else 'ZZZ',
                },
                'cac:RegistrationAddress': self._get_address_node({'partner': commercial_partner}),
            },
            'cac:Contact': {
                'cbc:ID': {'_text': partner.id},
                'cbc:Name': {'_text': partner.name},
                'cbc:Telephone': {'_text': partner.phone},
                'cbc:ElectronicMail': {'_text': partner.email},
            }
        }