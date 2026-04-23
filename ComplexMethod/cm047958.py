def _l10n_it_edi_check_exoneration_with_no_tax(self):
        for tax in self:
            if tax.country_id.code == 'IT':
                if tax.amount_type == 'percent' and tax.amount == 0 and not (tax.l10n_it_exempt_reason and html2plaintext(tax.invoice_legal_notes)):
                    raise ValidationError(_("If the tax amount is 0%, you must enter the exoneration code and the related legal notes."))
                if tax.l10n_it_exempt_reason == 'N6' and tax._l10n_it_is_split_payment():
                    raise UserError(_("Split Payment is not compatible with exoneration of kind 'N6'"))