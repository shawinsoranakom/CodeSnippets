def _assert_tax_totals_summary(self, tax_totals, expected_results, soft_checking=False):
        """ Assert the tax totals.
        :param tax_totals:          The tax totals computed from _get_tax_totals_summary in account.tax.
        :param expected_results:    The expected values.
        :param soft_checking:       Limit the asserted values to the ones in 'expected_results' and don't go deeper inside the dictionary.
        """
        def fix_monetary_value(current_values, expected_values, monetary_fields):
            for key, current_value in current_values.items():
                if not isinstance(expected_values.get(key), float):
                    continue
                expected_value = expected_values[key]
                currency = monetary_fields.get(key)
                if current_value is not None and currency.is_zero(current_value - expected_value):
                    current_values[key] = expected_value

        currency = self.env['res.currency'].browse(tax_totals['currency_id'])
        company_currency = self.env['res.currency'].browse(tax_totals['company_currency_id'])
        multi_currency = tax_totals['currency_id'] != tax_totals['company_currency_id']
        excluded_fields = set() if multi_currency else {
            'tax_amount',
            'base_amount',
            'display_base_amount',
            'company_currency_id',
            'total_amount',
        }
        excluded_fields.add('display_in_company_currency')
        excluded_fields.add('group_name')
        excluded_fields.add('group_label')
        excluded_fields.add('involved_tax_ids')
        excluded_fields.add('company_currency_pd')
        excluded_fields.add('currency_pd')
        excluded_fields.add('has_tax_groups')
        monetary_fields = {
            'tax_amount_currency': currency,
            'tax_amount': company_currency,
            'base_amount_currency': currency,
            'base_amount': company_currency,
            'display_base_amount_currency': currency,
            'display_base_amount': company_currency,
            'total_amount_currency': currency,
            'total_amount': company_currency,
            'cash_rounding_base_amount_currency': currency,
            'cash_rounding_base_amount': company_currency,
            'non_deductible_tax_amount_currency': currency,
            'non_deductible_tax_amount': company_currency,
        }

        current_values = {k: len(v) if k == 'subtotals' else v for k, v in tax_totals.items() if k not in excluded_fields}
        expected_values = {k: len(v) if k == 'subtotals' else v for k, v in expected_results.items()}
        if soft_checking:
            current_values = {k: v for k, v in current_values.items() if k in expected_values}

        fix_monetary_value(current_values, expected_values, monetary_fields)
        self.assertEqual(current_values, expected_values)
        if soft_checking:
            return

        for subtotal, expected_subtotal in zip(tax_totals['subtotals'], expected_results['subtotals']):
            current_values = {k: len(v) if k == 'tax_groups' else v for k, v in subtotal.items() if k not in excluded_fields}
            expected_values = {k: len(v) if k == 'tax_groups' else v for k, v in expected_subtotal.items()}
            fix_monetary_value(current_values, expected_values, monetary_fields)
            self.assertEqual(current_values, expected_values)
            for tax_group, expected_tax_group in zip(subtotal['tax_groups'], expected_subtotal['tax_groups']):
                current_tax_group = {k: v for k, v in tax_group.items() if k not in excluded_fields}
                fix_monetary_value(current_tax_group, expected_tax_group, monetary_fields)
                self.assertDictEqual(current_tax_group, expected_tax_group)