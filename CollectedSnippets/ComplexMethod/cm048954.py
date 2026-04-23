def _get_myinvois_document_party_identification_node(self, vals):
        """ The id vals list must be filled with two values.
        The TIN, and then one of either:
            - Business registration number (BNR)
            - MyKad/MyTentera identification number (NRIC)
            - Passport number or MyPR/MyKAS identification number (PASSPORT)
            - (ARMY)
        Additionally, companies registered to use SST (sales & services tax) must provide their SST number.
        Finally, if a supplier is using TTX (tourism tax), once again that number must be provided.
        """
        partner = vals['partner']

        tin = partner._l10n_my_edi_get_tin_for_myinvois()

        # If the invoice's commercial partner uses a Generic TIN, set it to the correct generic TIN
        # depending on whether the invoice is self-billed or not.
        if vals['document_type_code'] in ('01', '02', '03', '04') and tin == 'EI00000000030' and vals['role'] == 'customer':
            tin = 'EI00000000020'  # For normal invoices, this partner TIN should be used
        elif vals['document_type_code'] in ('11', '12', '13', '14') and tin == 'EI00000000020' and vals['role'] == 'supplier':
            tin = 'EI00000000030'  # For self-billed invoices, this partner TIN should be used

        party_identification_node = [
            {
                'cbc:ID': {
                    '_text': tin,
                    'schemeID': 'TIN',
                }
            }
        ]

        if partner.l10n_my_identification_type and partner.l10n_my_identification_number:
            party_identification_node.append({
                'cbc:ID': {
                    '_text': partner.l10n_my_identification_number,
                    'schemeID': partner.l10n_my_identification_type,
                }
            })
            if partner.sst_registration_number:
                party_identification_node.append({
                    'cbc:ID': {
                        '_text': partner.sst_registration_number,
                        'schemeID': 'SST',
                    }
                })
            if partner.ttx_registration_number and vals['role'] == 'supplier':
                party_identification_node.append({
                    'cbc:ID': {
                        '_text': partner.ttx_registration_number,
                        'schemeID': 'TTX',
                    }
                })
        return party_identification_node