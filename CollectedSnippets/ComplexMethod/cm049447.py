def _get_l10n_in_invoice_label(self):
        self.ensure_one()
        exempt_types = {'exempt', 'nil_rated', 'non_gst'}
        if self.country_code != 'IN' or not self.is_sale_document(include_receipts=False):
            return
        gst_treatment = self.l10n_in_gst_treatment
        company = self.company_id
        tax_types = set(self.invoice_line_ids.tax_ids.mapped('l10n_in_tax_type'))
        if company.l10n_in_is_gst_registered and tax_types:
            if gst_treatment in ['overseas', 'special_economic_zone']:
                return 'Tax Invoice'
            elif tax_types.issubset(exempt_types):
                return 'Bill of Supply'
            elif tax_types.isdisjoint(exempt_types):
                return 'Tax Invoice'
            elif gst_treatment in ['unregistered', 'consumer']:
                return 'Invoice-cum-Bill of Supply'
        return 'Invoice'