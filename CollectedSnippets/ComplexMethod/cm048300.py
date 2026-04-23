def _l10n_se_check_payment_reference(self):
        for invoice in self:
            if (
                (invoice.payment_reference or invoice.state == 'posted')
                and invoice.partner_id
                and invoice.move_type == 'in_invoice'
                and invoice.partner_id.l10n_se_check_vendor_ocr
                and invoice.country_code == 'SE'
            ):
                try:
                    luhn.validate(invoice.payment_reference)
                except Exception:
                    raise ValidationError(_("Vendor require OCR Number as payment reference. Payment reference isn't a valid OCR Number."))