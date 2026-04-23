def _get_tax_exemption_reason(self, customer, supplier, tax):
        """ Returns the reason and code from the tax if available.
            If not, it falls back to the default tax exemption reason defined for the respective tax category code.

            Note: In Peppol, taxes should be grouped by tax category code but *not* by
            exemption reason, see https://docs.peppol.eu/poacc/billing/3.0/bis/#_calculation_of_vat
        """

        if tax and (code := tax.ubl_cii_tax_exemption_reason_code):
            return {
                'tax_exemption_reason_code': code,
                'tax_exemption_reason': TAX_EXEMPTION_MAPPING.get(code, _("Exempt from tax") if tax.ubl_cii_requires_exemption_reason else None),
            }

        tax_category_code = self._get_tax_category_code(customer, supplier, tax)
        tax_exemption_reason = tax_exemption_reason_code = None

        if not tax or tax_category_code == 'E':
            tax_exemption_reason = _("Exempt from tax")
        elif tax_category_code == 'G':
            tax_exemption_reason = _('Export outside the EU')
            tax_exemption_reason_code = 'VATEX-EU-G'
        elif tax_category_code == 'K':
            tax_exemption_reason = _('Intra-Community supply')
            tax_exemption_reason_code = 'VATEX-EU-IC'

        return {
            'tax_exemption_reason': tax_exemption_reason,
            'tax_exemption_reason_code': tax_exemption_reason_code,
        }