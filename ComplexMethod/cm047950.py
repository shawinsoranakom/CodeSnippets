def _l10n_hu_edi_check_invoices(self):
        hu_vat_regex = re.compile(r'(HU)?\d{8}-[1-5]-\d{2}')
        hu_bank_account_regex = re.compile(r'\d{8}-\d{8}-\d{8}|\d{8}-\d{8}|[A-Z]{2}\d{2}[0-9A-Za-z]{11,30}')

        # This contains all the advance invoices that correspond to final invoices in `self`.
        advance_invoices = self.filtered(lambda m: not m._is_downpayment()).invoice_line_ids._get_downpayment_lines().mapped('move_id')

        checks = {
            'company_vat_missing': {
                'records': self.company_id.filtered(lambda c: not c.vat),
                'message': _('Please set company VAT number!'),
                'action_text': _('View Company/ies'),
            },
            'company_vat_invalid': {
                'records': self.company_id.filtered(
                    lambda c: (
                        (c.vat and not hu_vat_regex.fullmatch(c.vat))
                        or (c.l10n_hu_group_vat and not hu_vat_regex.fullmatch(c.l10n_hu_group_vat))
                    )
                ),
                'message': _('Please enter the Hungarian VAT (and/or Group VAT) number in 12345678-1-12 format!'),
                'action_text': _('View Company/ies'),
            },
            'company_address_missing': {
                'records': self.company_id.filtered(lambda c: not c.country_id or not c.zip or not c.city or not c.street),
                'message': _('Please set company Country, Zip, City and Street!'),
                'action_text': _('View Company/ies'),
            },
            'company_not_huf': {
                'records': self.company_id.filtered(lambda c: c.currency_id.name not in ['HUF', 'EUR']),
                'message': _('Please use HUF or EUR as your company currency.'),
                'action_text': _('View Company/ies'),
            },
            'partner_bank_account_invalid': {
                'records': self.partner_bank_id.filtered(lambda p: not hu_bank_account_regex.fullmatch(p.acc_number)),
                'message': _('Please set a valid recipient bank account number!'),
                'action_text': _('View partner(s)'),
            },
            'partner_vat_missing': {
                'records': self.partner_id.commercial_partner_id.filtered(
                    lambda p: p.is_company and not p.vat
                ),
                'message': _('Please set partner Tax ID on company partners!'),
                'action_text': _('View partner(s)'),
            },
            'partner_vat_invalid': {
                'records': self.partner_id.commercial_partner_id.filtered(
                    lambda p: (
                        p.is_company and p.country_code == 'HU'
                        and (
                            (p.vat and not hu_vat_regex.fullmatch(p.vat))
                            or (p.l10n_hu_group_vat and not hu_vat_regex.fullmatch(p.l10n_hu_group_vat))
                        )
                    )
                ),
                'message': _('Please enter the Hungarian VAT (and/or Group VAT) number in 12345678-1-12 format!'),
                'action_text': _('View partner(s)'),
            },
            'partner_address_missing': {
                'records': self.partner_id.commercial_partner_id.filtered(
                    lambda p: p.is_company and (not p.country_id or not p.zip or not p.city or not p.street),
                ),
                'message': _('Please set partner Country, Zip, City and Street!'),
                'action_text': _('View partner(s)'),
            },
            'invoice_date_not_today': {
                'records': self.filtered(lambda m: m.invoice_date != fields.Date.context_today(m)),
                'message': _('Please set invoice date to today!'),
                'action_text': _('View invoice(s)'),
            },
            'invoice_chain_not_confirmed': {
                'records': self.env['account.move'].union(*[
                    move._l10n_hu_get_chain_base()._l10n_hu_get_chain_invoices().filtered(
                        lambda m: (
                            m.id < move.id
                            and m.l10n_hu_edi_state in [False, 'rejected', 'cancelled']
                            and m not in self
                        )
                    )
                    for move in self
                ]),
                'message': _('The following invoices appear to be earlier in the chain, but have not yet been sent. Please send them first.'),
                'action_text': _('View invoice(s)'),
            },
            'invoice_advance_not_paid': {
                'records': advance_invoices.filtered(
                    lambda m: (
                        m.payment_state not in ['in_payment', 'paid', 'partial']
                        or m.l10n_hu_edi_state in [False, 'rejected', 'cancelled']
                            and m not in self  # It's okay to send an advance and a final invoice together, as we sort by id before sending.
                    )
                ),
                'message': _('All advance invoices must be paid and sent to NAV before the final invoice is issued.'),
                'action_text': _('View advance invoice(s)'),
            },
            'invoice_line_not_one_vat_tax': {
                'records': self.filtered(
                    lambda m: any(
                        len(l.tax_ids.filtered(lambda t: t.l10n_hu_tax_type)) != 1
                        for l in m.invoice_line_ids.filtered(lambda l: l.display_type == 'product')
                    )
                ),
                'message': _('Please set exactly one VAT tax on each invoice line!'),
                'action_text': _('View invoice(s)'),
            },
            'invoice_line_non_vat_taxes_misconfigured': {
                'records': self.invoice_line_ids.tax_ids.filtered(
                    lambda t: not t.l10n_hu_tax_type and (not t.price_include or not t.include_base_amount)
                ),
                'message': _("Please set any non-VAT (excise) taxes to be 'Included in Price' and 'Affects subsequent taxes'!"),
                'action_text': _('View tax(es)'),
            },
            'invoice_line_vat_taxes_misconfigured': {
                'records': self.invoice_line_ids.tax_ids.filtered(
                    lambda t: t.l10n_hu_tax_type and not t.is_base_affected
                ),
                'message': _("Please set any VAT taxes to be 'Affected by previous taxes'!"),
                'action_text': _('View tax(es)'),
            },
        }

        errors = {
            f"l10n_hu_edi_{check}": {
                'message': values['message'],
                'action_text': values['action_text'],
                'action': values['records']._get_records_action(name=values['action_text']),
            }
            for check, values in checks.items()
            if values['records']
        }

        if companies_missing_credentials := self.company_id.filtered(lambda c: not c.l10n_hu_edi_server_mode):
            errors['l10n_hu_edi_company_credentials_missing'] = {
                'message': _('Please set NAV credentials in the Accounting Settings!'),
                'action_text': _('Open Accounting Settings'),
                'action': self.env.ref('account.action_account_config').with_company(companies_missing_credentials[0])._get_action_dict(),
            }
        return errors