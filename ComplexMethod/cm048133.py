def _compute_l10n_es_edi_is_required(self):
        for move in self:
            has_tax = True
            # Check it is not an importation invoice (which will be report through the DUA invoice)
            if move.is_purchase_document():
                taxes = move.invoice_line_ids.tax_ids
                has_tax = any(t.l10n_es_type and t.l10n_es_type != 'ignore' for t in taxes)
            move.l10n_es_edi_is_required = move.is_invoice() \
                                           and move.country_code == 'ES' \
                                           and move.company_id.l10n_es_sii_tax_agency \
                                           and has_tax