def _compute_l10n_in_warning(self):
        indian_invoice = self.filtered(lambda m: m.country_code == 'IN' and m.move_type != 'entry')
        line_filter_func = lambda line: line.display_type == 'product' and line.tax_ids and line._origin
        _xmlid_to_res_id = self.env['ir.model.data']._xmlid_to_res_id
        for move in indian_invoice:
            warnings = {}
            company = move.company_id
            action_name = _("Journal Item(s)")
            action_text = _("View Journal Item(s)")
            if company.l10n_in_tcs_feature or company.l10n_in_tds_feature:
                invalid_tax_lines = move._get_l10n_in_invalid_tax_lines()
                if company.l10n_in_tcs_feature and invalid_tax_lines:
                    warnings['lower_tcs_tax'] = {
                        'message': _("As the Partner's PAN missing/invalid apply TCS at the higher rate."),
                        'actions': invalid_tax_lines.with_context(tax_validation=True)._get_records_action(
                            name=action_name,
                            views=[(_xmlid_to_res_id("l10n_in.view_move_line_tree_hsn_l10n_in"), "list")],
                            domain=[('id', 'in', invalid_tax_lines.ids)],
                        ),
                        'action_text': action_text,
                    }

                if applicable_sections := move._get_l10n_in_tds_tcs_applicable_sections():
                    tds_tcs_applicable_lines = (
                        move.move_type == 'out_invoice'
                        and move._get_tcs_applicable_lines(move.invoice_line_ids)
                        or move.invoice_line_ids
                    )
                    warnings['tds_tcs_threshold_alert'] = {
                        'message': applicable_sections._get_warning_message(),
                        'action': tds_tcs_applicable_lines.with_context(
                            default_tax_type_use=True,
                            move_type=move.move_type == 'in_invoice'
                        )._get_records_action(
                            name=action_name,
                            domain=[('id', 'in', tds_tcs_applicable_lines.ids)],
                            views=[(_xmlid_to_res_id("l10n_in.view_move_line_list_l10n_in_withholding"), "list")]
                        ),
                        'action_text': action_text,
                    }

            if (
                company.l10n_in_is_gst_registered
                and company.l10n_in_hsn_code_digit
                and (filtered_lines := move.invoice_line_ids.filtered(line_filter_func))
            ):
                lines = self.env['account.move.line']
                for line in filtered_lines:
                    hsn_code = line.l10n_in_hsn_code
                    if (
                        not hsn_code
                        or (
                            not re.match(r'^\d{4}$|^\d{6}$|^\d{8}$', hsn_code)
                            or len(hsn_code) < int(company.l10n_in_hsn_code_digit)
                        )
                    ):
                        lines |= line._origin

                if lines:
                    digit_suffixes = {
                        '4': _("4 digits, 6 digits or 8 digits"),
                        '6': _("6 digits or 8 digits"),
                        '8': _("8 digits")
                    }
                    msg = _(
                        "Ensure that the HSN/SAC Code consists either %s in invoice lines",
                        digit_suffixes.get(company.l10n_in_hsn_code_digit, _("Invalid HSN/SAC Code digit"))
                    )
                    warnings['invalid_hsn_code_length'] = {
                        'message': msg,
                        'action': lines._get_records_action(
                            name=action_name,
                            views=[(_xmlid_to_res_id("l10n_in.view_move_line_tree_hsn_l10n_in"), "list")],
                            domain=[('id', 'in', lines.ids)]
                        ),
                        'action_text': action_text,
                    }

            move.l10n_in_warning = warnings
        (self - indian_invoice).l10n_in_warning = {}