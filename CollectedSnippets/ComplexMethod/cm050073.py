def _add_document_monetary_total_vals(self, vals):
        # Compute the monetary totals for the document
        def fixed_total_grouping_function(base_line, tax_data):
            if vals['fixed_taxes_as_allowance_charges'] and tax_data and tax_data['tax'].amount_type == 'fixed':
                return vals['total_grouping_function'](base_line, tax_data)

        for currency_suffix in ['', '_currency']:
            for key in ['total_allowance', 'total_charge', 'total_lines']:
                vals[f'{key}{currency_suffix}'] = 0.0

        for base_line in vals['base_lines']:
            aggregated_tax_details = self.env['account.tax']._aggregate_base_line_tax_details(base_line, fixed_total_grouping_function)

            for currency_suffix in ['', '_currency']:
                base_line_total_excluded = \
                    base_line['tax_details'][f'total_excluded{currency_suffix}'] \
                    + base_line['tax_details'][f'delta_total_excluded{currency_suffix}'] \
                    + sum(
                        tax_details[f'tax_amount{currency_suffix}']
                        for grouping_key, tax_details in aggregated_tax_details.items()
                        if grouping_key
                    )

                if self._is_document_allowance_charge(base_line):
                    if base_line_total_excluded < 0.0:
                        vals[f'total_allowance{currency_suffix}'] += -base_line_total_excluded
                    else:
                        vals[f'total_charge{currency_suffix}'] += base_line_total_excluded
                else:
                    vals[f'total_lines{currency_suffix}'] += base_line_total_excluded

        for currency_suffix in ['', '_currency']:
            vals[f'tax_exclusive_amount{currency_suffix}'] = vals[f'total_lines{currency_suffix}'] \
                + vals[f'total_charge{currency_suffix}'] \
                - vals[f'total_allowance{currency_suffix}']

        def non_fixed_total_grouping_function(base_line, tax_data):
            if vals['fixed_taxes_as_allowance_charges'] and tax_data and tax_data['tax'].amount_type == 'fixed':
                return None
            return vals['total_grouping_function'](base_line, tax_data)

        base_lines_aggregated_tax_details = self.env['account.tax']._aggregate_base_lines_tax_details(vals['base_lines'], non_fixed_total_grouping_function)
        aggregated_tax_details = self.env['account.tax']._aggregate_base_lines_aggregated_values(base_lines_aggregated_tax_details)
        for currency_suffix in ['', '_currency']:
            vals[f'total_tax_amount{currency_suffix}'] = sum(
                    tax_details[f'tax_amount{currency_suffix}']
                    for grouping_key, tax_details in aggregated_tax_details.items()
                    if grouping_key
                )
            vals[f'tax_inclusive_amount{currency_suffix}'] = vals[f'tax_exclusive_amount{currency_suffix}'] + vals[f'total_tax_amount{currency_suffix}']

        # Cash rounding for 'add_invoice_line' cash rounding strategy
        # (For the 'biggest_tax' strategy the amounts are directly included in the tax amounts.)
        for currency_suffix in ['', '_currency']:
            vals[f'cash_rounding_base_amount{currency_suffix}'] = 0.0
            for base_line in vals.setdefault('cash_rounding_base_lines', []):
                tax_details = base_line['tax_details']
                vals[f'cash_rounding_base_amount{currency_suffix}'] += tax_details[f'total_excluded{currency_suffix}']