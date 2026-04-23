def _get_tax_details(self, base_lines, company, tax_lines=None):
        AccountTax = self.env['account.tax']
        tax_details_functions = AccountTax._l10n_es_edi_verifactu_get_tax_details_functions(company)
        base_line_filter = tax_details_functions['base_line_filter']
        total_grouping_function = tax_details_functions['total_grouping_function']
        tax_details_grouping_function = tax_details_functions['tax_details_grouping_function']

        base_lines = [base_line for base_line in base_lines if base_line_filter(base_line)]

        AccountTax._add_tax_details_in_base_lines(base_lines, company)
        AccountTax._round_base_lines_tax_details(base_lines, company, tax_lines=tax_lines)

        # Totals
        base_lines_aggregated_values_for_totals = AccountTax._aggregate_base_lines_tax_details(base_lines, total_grouping_function)
        totals = AccountTax._aggregate_base_lines_aggregated_values(base_lines_aggregated_values_for_totals)[True]

        # Tax details
        base_lines_aggregated_values_for_tax_details = AccountTax._aggregate_base_lines_tax_details(base_lines, tax_details_grouping_function)
        tax_details = AccountTax._aggregate_base_lines_aggregated_values(base_lines_aggregated_values_for_tax_details)

        return {
            'base_amount': totals['base_amount'],
            'tax_amount': totals['tax_amount'],
            'tax_details': {key: tax_detail for key, tax_detail in tax_details.items() if key},
            'tax_details_per_record': {
                frozendict(base_line): {key: tax_detail for key, tax_detail in tax_details.items() if key}
                for base_line, tax_details in base_lines_aggregated_values_for_tax_details
            },
        }