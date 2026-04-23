def _ubl_add_party_legal_entity_nodes(self, vals):
        # EXTENDS account.edi.ubl
        super()._ubl_add_party_legal_entity_nodes(vals)
        nodes = vals['party_node']['cac:PartyLegalEntity']
        partner = vals['party_vals']['partner']
        commercial_partner = partner.commercial_partner_id

        if commercial_partner.peppol_eas in ('0106', '0190'):
            nl_id = commercial_partner.peppol_endpoint
        else:
            nl_id = commercial_partner.company_registry

        if commercial_partner.country_code == 'NL' and nl_id:
            # For NL, VAT can be used as a Peppol endpoint, but KVK/OIN has to be used as PartyLegalEntity/CompanyID
            # To implement a workaround on stable, company_registry field is used without recording whether
            # the number is a KVK or OIN, and the length of the number (8 = KVK, 20 = OIN) is used to determine the type
            nodes.append({
                'cbc:RegistrationName': {'_text': commercial_partner.name},
                'cbc:CompanyID': {
                    '_text': nl_id,
                    'schemeID': '0190' if len(nl_id) == 20 else '0106',
                },
            })
        elif commercial_partner.country_code == 'LU' and commercial_partner.company_registry:
            nodes.append({
                'cbc:RegistrationName': {'_text': commercial_partner.name},
                'cbc:CompanyID': {
                    '_text': commercial_partner.company_registry,
                    'schemeID': None,
                },
            })
        elif commercial_partner.country_code == 'SE' and commercial_partner.company_registry:
            nodes.append({
                'cbc:RegistrationName': {'_text': commercial_partner.name},
                'cbc:CompanyID': {
                    '_text': ''.join(char for char in commercial_partner.company_registry if char.isdigit()),
                },
            })
        elif commercial_partner.country_code == 'BE' and commercial_partner.company_registry:
            nodes.append({
                'cbc:RegistrationName': {'_text': commercial_partner.name},
                'cbc:CompanyID': {
                    '_text': be_vat.compact(commercial_partner.company_registry),
                    'schemeID': '0208',
                },
            })
        elif (
            commercial_partner.country_code == 'DK'
            and commercial_partner.peppol_eas == '0184'
            and commercial_partner.peppol_endpoint
        ):
            nodes.append({
                'cbc:RegistrationName': {'_text': commercial_partner.name},
                'cbc:CompanyID': {
                    '_text': commercial_partner.peppol_endpoint,
                    'schemeID': '0184',
                },
            })
        elif commercial_partner.vat and commercial_partner.vat != '/':
            nodes.append({
                'cbc:RegistrationName': {'_text': commercial_partner.name},
                'cbc:CompanyID': {
                    '_text': commercial_partner.vat,
                    'schemeID': None,
                },
            })
        elif commercial_partner.peppol_endpoint:
            nodes.append({
                'cbc:RegistrationName': {'_text': commercial_partner.name},
                'cbc:CompanyID': {
                    '_text': commercial_partner.peppol_endpoint,
                    'schemeID': None,
                },
            })