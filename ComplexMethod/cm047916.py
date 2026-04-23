def _add_invoice_base_lines_vals(self, vals):
        # OVERRIDE account_edi_xml_ubl_20.py
        currency_9_dp = vals['currency_id']
        invoice = vals['invoice']

        # Compute values for invoice lines. In Jordan, because the web-service has absolutely no tolerance,
        # what we do is: use round per line with 9 decimals (yes!)
        base_amls = invoice.line_ids.filtered(lambda line: line.display_type == 'product')
        base_lines = [invoice._prepare_product_base_line_for_taxes_computation(line) for line in base_amls]
        epd_amls = invoice.line_ids.filtered(lambda line: line.display_type == 'epd')
        base_lines += [invoice._prepare_epd_base_line_for_taxes_computation(line) for line in epd_amls]
        cash_rounding_amls = invoice.line_ids.filtered(lambda line: line.display_type == 'rounding' and not line.tax_repartition_line_id)
        base_lines += [invoice._prepare_cash_rounding_base_line_for_taxes_computation(line) for line in cash_rounding_amls]

        AccountTax = self.env['account.tax']
        for base_line in base_lines:
            base_line['currency_id'] = currency_9_dp
            AccountTax._add_tax_details_in_base_line(base_line, base_line['record'].company_id, 'round_per_line')

        # Round to 9 decimals
        AccountTax._round_base_lines_tax_details(base_lines, company=invoice.company_id)

        # raw_total_* values need to calculated with `round_globally` because these values should not be rounded per line
        # However, taxes need to be calculated with `round_per_line` so that _round_base_lines_tax_details does not
        # end up generating lines taxes using unrounded base amounts
        new_base_lines = [base_line.copy() for base_line in base_lines]
        for base_line, new_base_line in zip(base_lines, new_base_lines):
            AccountTax._add_tax_details_in_base_line(new_base_line, new_base_line['record'].company_id, 'round_globally')
            for key in [
                'raw_total_excluded_currency',
                'raw_total_excluded',
                'raw_total_included_currency',
                'raw_total_included',
            ]:
                base_line['tax_details'][key] = new_base_line['tax_details'][key]

        vals['base_lines'] = base_lines
        self._add_base_lines_edi_ids(vals)