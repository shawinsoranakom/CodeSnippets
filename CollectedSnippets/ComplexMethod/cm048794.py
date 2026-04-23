def _round_raw_gross_total_excluded_and_discount(
        self,
        base_lines,
        company,
        in_foreign_currency=True,
    ):
        if not base_lines:
            return

        suffix_currency = base_lines[0]['currency_id'] if in_foreign_currency else company.currency_id
        suffix = '_currency' if in_foreign_currency else ''

        # Raw rounding.
        current_gross_total_excluded = 0.0
        current_discount_amount = 0.0
        current_raw_discount_amount = 0.0
        for base_line in base_lines:
            tax_details = base_line['tax_details']
            gross_total_excluded = tax_details[f'gross_total_excluded{suffix}'] = float_round(
                value=tax_details[f'raw_gross_total_excluded{suffix}'],
                precision_rounding=suffix_currency.rounding,
            )
            current_gross_total_excluded += gross_total_excluded

            raw_discount_amount = tax_details[f'raw_discount_amount{suffix}']
            discount_amount = tax_details[f'discount_amount{suffix}'] = float_round(
                value=raw_discount_amount,
                precision_rounding=suffix_currency.rounding,
            )
            current_discount_amount += discount_amount
            current_raw_discount_amount += raw_discount_amount

        # Collect the 'total_excluded'.
        def grouping_function(base_line, tax_data):
            return True

        base_lines_aggregated_values = self._aggregate_base_lines_tax_details(base_lines, grouping_function)
        values_per_grouping_key = self._aggregate_base_lines_aggregated_values(base_lines_aggregated_values)
        expected_total_excluded = sum(
            values[f'total_excluded{suffix}']
            for values in values_per_grouping_key.values()
        )

        # Fix rounding issues for 'gross_total_excluded'.
        # Note: 'expected_gross_total_excluded' contains also the 'delta_total_excluded' to put all the difference due to the
        # global taxes rounding on it instead of putting it on 'discount_amount' since the discount won't always be there.
        expected_gross_total_excluded = expected_total_excluded + float_round(
            value=current_raw_discount_amount,
            precision_rounding=suffix_currency.rounding,
        )

        target_factors = [
            {
                'factor': 1.0,  # By default, we avoid to have more than one cent as a difference per line.
                'base_line': base_line,
            }
            for base_line in base_lines
        ]
        amounts_to_distribute = self._distribute_delta_amount_smoothly(
            precision_digits=suffix_currency.decimal_places,
            delta_amount=expected_gross_total_excluded - current_gross_total_excluded,
            target_factors=target_factors,
        )
        for target_factor, amount_to_distribute in zip(target_factors, amounts_to_distribute):
            base_line = target_factor['base_line']
            base_line['tax_details'][f'gross_total_excluded{suffix}'] += amount_to_distribute

        # Fix rounding issues for 'discount_amount'.
        expected_discount_amount = expected_gross_total_excluded - expected_total_excluded
        amounts_to_distribute = self._distribute_delta_amount_smoothly(
            precision_digits=suffix_currency.decimal_places,
            delta_amount=expected_discount_amount - current_discount_amount,
            target_factors=target_factors,
        )
        for target_factor, amount_to_distribute in zip(target_factors, amounts_to_distribute):
            base_line = target_factor['base_line']
            base_line['tax_details'][f'discount_amount{suffix}'] += amount_to_distribute