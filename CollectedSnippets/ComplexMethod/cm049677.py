def _get_tax_category_code(self, customer, supplier, tax):
        """ Override to include/update values specific to ZATCA's UBL 2.1 specs """
        if supplier.country_id.code == 'SA':
            if tax and tax.amount != 0:
                return 'S'
            elif tax and tax.l10n_sa_exemption_reason_code in TAX_EXEMPTION_CODES:
                return 'E'
            elif tax and tax.l10n_sa_exemption_reason_code in TAX_ZERO_RATE_CODES:
                return 'Z'
            else:
                return 'O'
        return super()._get_tax_category_code(customer, supplier, tax)