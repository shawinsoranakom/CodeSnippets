def _l10n_jo_validate_fields(self):
        def has_non_digit_vat(partner, partner_type, error_msgs):
            if partner.vat and not partner.vat.isdigit():
                error_msgs.append(_("JoFotara portal cannot process %s VAT with non-digit characters in it", partner_type))

        error_msgs = []

        if not self.preferred_payment_method_line_id:
            error_msgs.append(_("Please select a payment method before submission."))
        if not self.l10n_jo_edi_invoice_type:
            error_msgs.append(_("Please select an invoice type before submitting this invoice to JoFotara."))

        customer = self.partner_id
        has_non_digit_vat(customer, 'customer', error_msgs)

        supplier = self.company_id.partner_id.commercial_partner_id
        has_non_digit_vat(supplier, 'supplier', error_msgs)

        if self.move_type == 'out_refund':
            if not self.reversed_entry_id:
                error_msgs.append(_('Please use "Reversal of" to link this credit note with an Invoice'))
            elif self.currency_id != self.reversed_entry_id.currency_id:
                error_msgs.append(_("Please make sure the currency of the credit note is the same as the related invoice"))

            if not self.ref:
                error_msgs.append(_('Please make sure the "Customer Reference" contains the reason for the return'))

        if any(
            line.display_type not in ('line_section', 'line_subsection', 'line_note')
            and (line.quantity < 0 or line.price_unit < 0)
            for line in self.invoice_line_ids
        ):
            error_msgs.append(_("JoFotara portal cannot process negative quantity nor negative price on invoice lines"))

        for line in self.invoice_line_ids.filtered(lambda line: line.display_type not in ('line_section', 'line_subsection', 'line_note')):
            if self.company_id.l10n_jo_edi_taxpayer_type == 'income' and len(line.tax_ids) != 0:
                error_msgs.append(_("No taxes are allowed on invoice lines for taxpayers unregistered in the sales tax"))
            elif self.company_id.l10n_jo_edi_taxpayer_type == 'sales' and len(line.tax_ids) != 1:
                error_msgs.append(_("One general tax per invoice line is expected for taxpayers registered in the sales tax"))
            elif self.company_id.l10n_jo_edi_taxpayer_type == 'special' and len(line.tax_ids) != 2:
                error_msgs.append(_("One special and one general tax per invoice line is expected for taxpayers registered in the special tax"))

        return "\n".join(error_msgs)