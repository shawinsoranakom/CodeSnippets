def _get_l10n_in_tds_tcs_applicable_sections(self):
        def _group_by_section_alert(invoice_lines):
            group_by_lines = {}
            for line in invoice_lines:
                group_key = line.account_id.sudo().l10n_in_tds_tcs_section_id
                if group_key and not line.company_currency_id.is_zero(line.price_total):
                    group_by_lines.setdefault(group_key, [])
                    group_by_lines[group_key].append(line)
            return group_by_lines

        def _is_section_applicable(section_alert, threshold_sums, invoice_currency_rate, lines):
            lines_total = sum(
                (line.price_total * invoice_currency_rate) if section_alert.consider_amount == 'total_amount' else line.balance
                for line in lines
            )
            if section_alert.is_aggregate_limit:
                aggregate_period_key = section_alert.consider_amount == 'total_amount' and 'price_total' or 'balance'
                aggregate_total = threshold_sums.get(section_alert.aggregate_period, {}).get(aggregate_period_key)
                if self.state == 'draft':
                    aggregate_total += lines_total
                if aggregate_total > section_alert.aggregate_limit:
                    return True
            return (
                section_alert.is_per_transaction_limit
                and lines_total > section_alert.per_transaction_limit
            )

        if self.country_code == 'IN' and self.move_type in ['in_invoice', 'out_invoice']:
            warning = set()
            commercial_partner_id = self.commercial_partner_id
            if commercial_partner_id.l10n_in_pan_entity_id.tds_deduction == 'no':
                invoice_lines = self.invoice_line_ids.filtered(lambda l: l.account_id.l10n_in_tds_tcs_section_id.tax_source_type != 'tds')
            else:
                invoice_lines = self.invoice_line_ids
            existing_section = (
                self.l10n_in_withhold_move_ids.line_ids + self.line_ids
            ).tax_ids.l10n_in_section_id
            for section_alert, lines in _group_by_section_alert(invoice_lines).items():
                if (
                    (section_alert not in existing_section
                    or self._get_tcs_applicable_lines(lines))
                    and self._l10n_in_is_warning_applicable(section_alert)
                    and _is_section_applicable(
                        section_alert,
                        self._get_sections_aggregate_sum_by_pan(
                            section_alert,
                            commercial_partner_id
                        ),
                        self.invoice_currency_rate,
                        lines
                    )
                ):
                    warning.add(section_alert.id)
            return self.env['l10n_in.section.alert'].browse(warning)