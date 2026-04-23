def _get_alerts(self, moves, moves_data):
        def _is_valid_nilvera_name(move):
            _, parts = move._get_sequence_format_param(move.name)

            return (
                parts['year'] != 0
                and parts['year_length'] == 4
                and parts['seq'] != 0
                and re.match(r'^[A-Za-z0-9]{3}[^A-Za-z0-9]?$', parts['prefix1'])
            )

        alerts = super()._get_alerts(moves, moves_data)

        # Filter for moves that have 'tr_nilvera' in their EDI data
        tr_nilvera_moves = moves.filtered(lambda m: 'tr_nilvera' in moves_data[m]['extra_edis'])

        # Show alert if the current company is in Türkiye and test mode is enabled for Nilvera
        if self.env.company.account_fiscal_country_id.code == 'TR' and self.env.company.l10n_tr_nilvera_use_test_env:
            alerts['l10n_tr_nilvera_einvoice_test_mode'] = {
                'level': 'info',
                'message': _("Testing mode is enabled."),
            }

        if tr_companies_missing_required_codes := tr_nilvera_moves.company_id.filtered(lambda c: c.country_code == 'TR' and not (c.partner_id.category_id.parent_id and self.env["res.partner.category"]._get_l10n_tr_official_mandatory_categories())):
            alerts["tr_companies_missing_required_codes"] = {
                "message": _("Please ensure that your company contact has either the 'MERSISNO' or 'TICARETSICILNO' tag with a value assigned."),
                "action_text": _("View Company(s)"),
                "action": tr_companies_missing_required_codes.partner_id._get_records_action(name=_("Check tags on company(s)")),
                "level": "danger",
            }

        # Alert if company is missing required data (country = TR, and tax ID, city, state, street)
        if tr_companies_missing_required_fields := tr_nilvera_moves.filtered(
            lambda m: (
                not m.company_id.vat
                or not m.company_id.street
                or not m.company_id.city
                or not m.company_id.state_id
                or m.company_id.country_code != 'TR'
            )
        ).company_id:
            alerts["tr_companies_missing_required_fields"] = {
                'level': 'danger',
                "message": _(
                    "The following company(s) either do not have their country set as Türkiye "
                    "or are missing at least one of these fields: Tax ID, Street, City, or State"
                ),
                "action_text": _("View Company(s)"),
                "action": tr_companies_missing_required_fields._get_records_action(name=_(
                    "Check Tax ID, City, Street, State, and Country or Company(s)"
                )),
            }

        # Alert if partner is missing required data (tax ID, street, city, state, country)
        if tr_partners_missing_required_fields := self._get_l10n_tr_tax_partner_address_alert(tr_nilvera_moves):
            alerts["tr_partners_missing_required_fields"] = tr_partners_missing_required_fields

        # Alert if partner is missing required tax office
        if tr_partners_missing_tax_office := self._get_l10n_tr_tax_partner_tax_office_alert(tr_nilvera_moves):
            alerts["tr_partners_missing_tax_office"] = tr_partners_missing_tax_office

        # Alert if TR company is missing required tax office
        if tr_companies_missing_tax_office := self._get_l10n_tr_tax_company_tax_office_alert(tr_nilvera_moves):
            alerts["tr_companies_missing_tax_office"] = tr_companies_missing_tax_office

        # Alert if partner does not use UBL TR e-invoice format or has not checked Nilvera status
        if tr_partners_invalid_edi_or_status := tr_nilvera_moves.filtered(
            lambda m: (
                m.partner_id.invoice_edi_format != 'ubl_tr'
                or m.partner_id.l10n_tr_nilvera_customer_status == 'not_checked'
            )
        ).partner_id:
            alerts["tr_partners_invalid_edi_or_status"] = {
                'level': 'danger',
                "message": _(
                    "The following partner(s) either do not have the e-invoice format UBL TR 1.2 "
                    "or have not checked their Nilvera Status"
                ),
                "action_text": _("View Partner(s)"),
                "action": tr_partners_invalid_edi_or_status._get_records_action(
                    name=_("Check e-Invoice Format or Nilvera Status on Partner(s)"
                )),
            }

        if tr_invalid_subscription_dates := moves.filtered(
            lambda move: move._l10n_tr_nilvera_einvoice_check_invalid_subscription_dates()
        ):
            alerts["tr_invalid_subscription_dates"] = {
                'level': 'danger',
                "message": _(
                    "The following invoice(s) need to have the same Start Date and End Date "
                    "on all their respective Invoice Lines."
                ),
                "action_text": _("View Invoice(s)"),
                "action": tr_invalid_subscription_dates._get_records_action(
                    name=_("Check data on Invoice(s)"),
                ),
            }

        if invalid_negative_lines := tr_nilvera_moves.filtered(
            lambda move: move._l10n_tr_nilvera_einvoice_check_negative_lines(),
        ):
            alerts["critical_invalid_negative_lines"] = {
                "level": "danger",
                "message": _("Nilvera portal cannot process negative quantity nor negative price on invoice lines"),
                "action_text": _("View Invoice(s)"),
                "action": invalid_negative_lines._get_records_action(name=_("Check data on Invoice(s)")),
            }

        if moves_with_invalid_name := tr_nilvera_moves.filtered(lambda move: not _is_valid_nilvera_name(move)):
            alerts['tr_moves_with_invalid_name'] = {
                'level': 'danger',
                'message': _(
                    "The invoice name must follow the format when sending to Nilvera: 3 alphanumeric characters, "
                    "followed by the year, and then a sequential number. Example: INV/2025/000001",
                ),
                'action_text': _("View Invoice(s)"),
                'action': moves_with_invalid_name._get_records_action(name=_("Check name on Invoice(s)")),
            }

        return alerts