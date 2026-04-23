def _ubl_add_values_tax_totals(self, vals):
        """ Add
            'vals' -> '_ubl_values' -> 'tax_totals'
            'vals' -> '_ubl_values' -> 'withholding_tax_totals'

        'tax_totals' will contain the total and subtotals for not-withholding taxes.
        'withholding_tax_totals' will contain the total and subtotals for withholding taxes.

        TO BE REMOVED IN MASTER

        :param vals:                        Some custom data.
        """
        AccountTax = self.env['account.tax']
        base_lines = vals['base_lines']
        company = vals['company']
        company_currency = company.currency_id
        currency = vals['currency_id']

        ubl_values = vals['_ubl_values']
        ubl_values['tax_totals'] = {}
        ubl_values['tax_totals_currency'] = {}
        ubl_values['withholding_tax_totals'] = {}
        ubl_values['withholding_tax_totals_currency'] = {}

        def tax_category_grouping_function(base_line, tax_data, sub_currency):
            tax_grouping_key = self._ubl_default_tax_category_grouping_key(base_line, tax_data, vals, sub_currency)
            if not tax_grouping_key:
                return
            return self._ubl_default_tax_subtotal_tax_category_grouping_key(tax_grouping_key, vals)

        def tax_subtotal_grouping_function(base_line, tax_data, sub_currency):
            tax_category_grouping_key = tax_category_grouping_function(base_line, tax_data, sub_currency)
            if not tax_category_grouping_key:
                return
            return self._ubl_default_tax_subtotal_grouping_key(tax_category_grouping_key, vals)

        def tax_totals_grouping_function(base_line, tax_data, sub_currency):
            tax_subtotal_grouping_key = tax_subtotal_grouping_function(base_line, tax_data, sub_currency)
            if not tax_subtotal_grouping_key:
                return
            return self._ubl_default_tax_total_grouping_key(tax_subtotal_grouping_key, vals)

        for sub_currency, suffix in ((currency, '_currency'), (company_currency, '')):

            # tax_totals / withholding_tax_totals

            base_lines_aggregated_values = AccountTax._aggregate_base_lines_tax_details(
                base_lines=base_lines,
                grouping_function=lambda base_line, tax_data: tax_totals_grouping_function(base_line, tax_data, sub_currency),
            )
            values_per_grouping_key = AccountTax._aggregate_base_lines_aggregated_values(base_lines_aggregated_values)
            for grouping_key, values in values_per_grouping_key.items():
                if not grouping_key:
                    continue

                if grouping_key['is_withholding']:
                    target_key = f'withholding_tax_totals{suffix}'
                    sign = -1
                else:
                    target_key = f'tax_totals{suffix}'
                    sign = 1

                ubl_values[target_key][frozendict(grouping_key)] = {
                    **grouping_key,
                    'amount': sign * values[f'tax_amount{suffix}'],
                    'subtotals': {},
                }

            # tax_subtotals

            base_lines_aggregated_values = AccountTax._aggregate_base_lines_tax_details(
                base_lines=base_lines,
                grouping_function=lambda base_line, tax_data: tax_subtotal_grouping_function(base_line, tax_data, sub_currency),
            )
            values_per_grouping_key = AccountTax._aggregate_base_lines_aggregated_values(base_lines_aggregated_values)
            for grouping_key, values in values_per_grouping_key.items():
                if not grouping_key:
                    continue

                if grouping_key['is_withholding']:
                    target_key = f'withholding_tax_totals{suffix}'
                    sign = -1
                else:
                    target_key = f'tax_totals{suffix}'
                    sign = 1

                tax_total_grouping_key = self._ubl_default_tax_total_grouping_key(grouping_key, vals)
                if not tax_total_grouping_key:
                    continue

                tax_total_values = ubl_values[target_key][frozendict(tax_total_grouping_key)]
                tax_total_values['subtotals'][frozendict(grouping_key)] = {
                    **grouping_key,
                    'base_amount': values[f'base_amount{suffix}'],
                    'tax_amount': sign * values[f'tax_amount{suffix}'],
                    'tax_categories': {},
                }

            # tax_categories

            base_lines_aggregated_values = AccountTax._aggregate_base_lines_tax_details(
                base_lines=base_lines,
                grouping_function=lambda base_line, tax_data: tax_category_grouping_function(base_line, tax_data, sub_currency),
            )
            values_per_grouping_key = AccountTax._aggregate_base_lines_aggregated_values(base_lines_aggregated_values)
            for grouping_key, values in values_per_grouping_key.items():
                if not grouping_key:
                    continue

                if grouping_key['is_withholding']:
                    target_key = f'withholding_tax_totals{suffix}'
                    sign = -1
                else:
                    target_key = f'tax_totals{suffix}'
                    sign = 1

                tax_subtotal_grouping_key = self._ubl_default_tax_subtotal_grouping_key(grouping_key, vals)
                if not tax_subtotal_grouping_key:
                    continue

                tax_total_grouping_key = self._ubl_default_tax_total_grouping_key(tax_subtotal_grouping_key, vals)
                if not tax_total_grouping_key:
                    continue

                tax_total_values = ubl_values[target_key][frozendict(tax_total_grouping_key)]
                tax_total_values['subtotals'][frozendict(tax_subtotal_grouping_key)]['tax_categories'][frozendict(grouping_key)] = {
                    **grouping_key,
                    'base_amount': values[f'base_amount{suffix}'],
                    'tax_amount': sign * values[f'tax_amount{suffix}'],
                }

            for key in (f'withholding_tax_totals{suffix}', f'tax_totals{suffix}'):
                if not ubl_values[key]:
                    ubl_values[key][None] = {
                        'currency': sub_currency,
                        'amount': 0.0,
                        'subtotals': {},
                    }