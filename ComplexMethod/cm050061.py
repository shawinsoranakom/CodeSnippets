def _ubl_add_party_tax_scheme_nodes(self, vals):
        # EXTENDS account.edi.ubl
        super()._ubl_add_party_tax_scheme_nodes(vals)
        nodes = vals['party_node']['cac:PartyTaxScheme']
        partner = vals['party_vals']['partner']
        commercial_partner = partner.commercial_partner_id

        if commercial_partner.vat and commercial_partner.vat != '/':
            vat = commercial_partner.vat
            country_code = commercial_partner.country_id.code
            if country_code in GST_COUNTRY_CODES:
                tax_scheme_id = 'GST'
            else:
                tax_scheme_id = 'VAT'

            if country_code == 'HU' and not vat.upper().startswith('HU'):
                vat = 'HU' + vat[:8]

            nodes.append({
                'cbc:CompanyID': {'_text': vat},
                'cac:TaxScheme': {
                    'cbc:ID': {'_text': tax_scheme_id},
                },
            })
        elif commercial_partner.peppol_endpoint and commercial_partner.peppol_eas:
            # TaxScheme based on partner's EAS/Endpoint.
            nodes.append({
                'cbc:CompanyID': {'_text': commercial_partner.peppol_endpoint},
                'cac:TaxScheme': {
                    'cbc:ID': {'_text': commercial_partner.peppol_eas},
                },
            })