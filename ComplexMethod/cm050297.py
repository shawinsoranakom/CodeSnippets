def _l10n_eg_eta_prepare_address_data(self, partner, invoice, issuer=False):
        address = {
            'address': {
                'country': partner.country_id.code,
                'governate': partner.state_id.name or '',
                'regionCity': partner.city or '',
                'street': partner.street or '',
                'buildingNumber': partner.l10n_eg_building_no or '',
                'postalCode': partner.zip or '',
            },
            'name': partner.name,
        }
        if issuer:
            address['address']['branchID'] = invoice.journal_id.l10n_eg_branch_identifier or ''
        individual_type = self._l10n_eg_get_partner_tax_type(partner, issuer)
        address['type'] = individual_type or ''
        if invoice.amount_total >= invoice.company_id.l10n_eg_invoicing_threshold or individual_type != 'P':
            address['id'] = partner.vat or ''
        return address