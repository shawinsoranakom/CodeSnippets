def _l10n_it_edi_is_simplified(self):
        """
            Simplified Invoices are a way for the invoice issuer to create an invoice with limited data.
            Example: a consultant goes to the restaurant and wants the invoice instead of the receipt,
            to be able to deduct the expense from his Taxes. The Italian State allows the restaurant
            to issue a Simplified Invoice with the VAT number only, to speed up times, instead of
            requiring the address and other information about the buyer.
            The maximum threshold is 400 Euro, except for the forfettario tax regime (RF19), which can
            issue simplified invoices without the amount limit.
        """
        self.ensure_one()
        template_reference = self.env.ref('l10n_it_edi.account_invoice_it_simplified_FatturaPA_export', raise_if_not_found=False)
        buyer = self.commercial_partner_id
        checks = ['partner_address_missing', 'partner_vat_codice_fiscale_missing']
        return bool(
            template_reference
            and not self.l10n_it_edi_is_self_invoice
            and list(buyer._l10n_it_edi_export_check(checks).keys()) == ['l10n_it_edi_partner_address_missing']
            and (not buyer.country_id or buyer.country_id.code == 'IT')
            and (buyer.l10n_it_codice_fiscale or (buyer.vat and (buyer.vat[:2].upper() == 'IT' or buyer.vat[:2].isdecimal())))
            and (self.company_id.l10n_it_tax_system == 'RF19' or self.amount_total <= 400)
        )