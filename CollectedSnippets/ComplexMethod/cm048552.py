def _assert_sub_test_taxes_computation(self, results, expected_values):

        def compare_taxes_computation_values(sub_results, rounding):
            self.assertEqual(
                float_round(sub_results['total_included'], precision_rounding=rounding),
                float_round(expected_values['total_included'], precision_rounding=rounding),
            )
            self.assertEqual(
                float_round(sub_results['total_excluded'], precision_rounding=rounding),
                float_round(expected_values['total_excluded'], precision_rounding=rounding),
            )
            self.assertEqual(len(sub_results['taxes_data']), len(expected_values['taxes_data']))
            for tax_data, (expected_base, expected_tax) in zip(sub_results['taxes_data'], expected_values['taxes_data']):
                self.assertEqual(
                    float_round(tax_data['base_amount'], precision_rounding=rounding),
                    float_round(expected_base, precision_rounding=rounding),
                )
                self.assertEqual(
                    float_round(tax_data['tax_amount'], precision_rounding=rounding),
                    float_round(expected_tax, precision_rounding=rounding),
                )

        is_round_globally = results['rounding_method'] == 'round_globally'
        excluded_special_modes = results['excluded_special_modes'] or []
        rounding = 0.000001 if is_round_globally else 0.01
        compare_taxes_computation_values(results['results'], rounding)

        # Check the special modes in case of round_globally.
        if is_round_globally:
            # special_mode == 'total_excluded'.
            if 'total_excluded' not in excluded_special_modes:
                compare_taxes_computation_values(results['total_excluded_results'], rounding)
                delta = sum(
                    x['tax_amount']
                    for x in results['total_excluded_results']['taxes_data']
                    if x['tax']['price_include']
                )

                self.assertEqual(
                    float_round(
                        (results['total_excluded_results']['total_excluded'] + delta) / results['quantity'],
                        precision_rounding=rounding,
                    ),
                    float_round(results['price_unit'], precision_rounding=rounding),
                )

            # special_mode == 'total_included'.
            if 'total_included' not in excluded_special_modes:
                compare_taxes_computation_values(results['total_included_results'], rounding)
                delta = sum(
                    x['tax_amount']
                    for x in results['total_included_results']['taxes_data']
                    if not x['tax']['price_include']
                )

                self.assertEqual(
                    float_round(
                        (results['total_included_results']['total_included'] - delta) / results['quantity'],
                        precision_rounding=rounding,
                    ),
                    float_round(results['price_unit'], precision_rounding=rounding),
                )