def _l10n_vn_edi_check_invoice_configuration(self):
        """ Some checks that are used to avoid common errors before sending the invoice. """
        self.ensure_one()
        company = self.company_id
        commercial_partner = self.commercial_partner_id
        errors = []
        if not company.l10n_vn_edi_username or not company.l10n_vn_edi_password:
            errors.append(_('Sinvoice credentials are missing on company %s.', company.display_name))
        if not company.vat:
            errors.append(_('VAT number is missing on company %s.', company.display_name))
        company_phone = company.phone and self._l10n_vn_edi_format_phone_number(company.phone)
        if company_phone and not company_phone.isdecimal():
            errors.append(_('Phone number for company %s must only contain digits or +.', company.display_name))
        commercial_partner_phone = commercial_partner.phone and self._l10n_vn_edi_format_phone_number(commercial_partner.phone)
        if commercial_partner_phone and not commercial_partner_phone.isdecimal():
            errors.append(_('Phone number for partner %s must only contain digits or +.', commercial_partner.display_name))
        if not self.l10n_vn_edi_invoice_symbol:
            errors.append(_('The invoice symbol must be provided.'))
        if self.l10n_vn_edi_invoice_symbol and not self.l10n_vn_edi_invoice_symbol.invoice_template_id:
            errors.append(_("The invoice symbol's template must be provided."))
        if self.move_type == 'out_refund' and (not self.reversed_entry_id or not self.reversed_entry_id._l10n_vn_edi_is_sent()):
            errors.append(_('You can only send a credit note linked to a previously sent invoice.'))
        if not company.street or not company.state_id or not company.country_id:
            errors.append(_('The street, state and country of company %s must be provided.', company.display_name))
        if self.company_currency_id.name != 'VND':
            vnd = self.env.ref('base.VND')
            rate = vnd.with_context(date=self.invoice_date or self.date).rate
            if not vnd.active or rate == 1:
                errors.append(_('Please make sure that the VND currency is enabled, and that the exchange rates are set.'))
        return errors