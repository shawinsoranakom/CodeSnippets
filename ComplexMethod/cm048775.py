def _round_tax_details_base_lines(self, base_lines, company, mode='mixed'):
        """ Additional global rounding depending on if the taxes are included or excluded in price.

        This method does not modify the rounding in `taxes_data`, rather it computes an adjustment
        for `tax_details['total_excluded{_currency}']` and stores it as `tax_details['delta_total_excluded{_currency}']`.

        Suppose all taxes are price-included.
        Suppose two price-included taxes of 10%.
        Suppose a line having price_unit=100.0.
        The tax amount is computed as 100.0 / 1.2 * 0.1 = 8.333333333
        The base amount is computed as 100.0 - (2 * 8.333333333) = 83.333333334
        Without doing anything, we end up with a base of 83.33 and 2 * 8.33 as tax amounts.
        83.33 + 8.33 + 8.33 = 99.99.
        However, since all tax are price-included, we expect a base amount of 83.34 to reach the
        original 100.0.

        Manage price-excluded taxes.
        Suppose 2 lines, both having quantity=12.12, price_unit=12.12, tax=23%
        The base amount of each line is computed as round(12.12 * 12.12) = 146.89
        The expected base amount of the whole document is round(12.12 * 12.12 * 2) = 293.79
        The delta in term of base amount is 293.79 - 146.89 - 146.89 = 0.01

        [!] Mirror of the same method in account_tax.js.
        PLZ KEEP BOTH METHODS CONSISTENT WITH EACH OTHERS.

        :param base_lines:          A list of base lines generated using the '_prepare_base_line_for_taxes_computation' method.
        :param company:             The company owning the base lines.
        :param mode:                The mode to round taxes:
            * excluded:                 Round base and tax independently.
            * included:                 Round base + tax, then subtract the tax and round the base according the remaining amount.
            * mixed:                    Round 'excluded' or 'included' depending if the tax is price-included or not.
        """
        def grouping_function(base_line, tax_data):
            return {
                'currency': base_line['currency_id'],
                'is_refund': base_line['is_refund'],
                'computation_key': base_line['computation_key'],
            }

        base_lines_aggregated_values = self._aggregate_base_lines_tax_details(base_lines, grouping_function)
        values_per_grouping_key = self._aggregate_base_lines_aggregated_values(base_lines_aggregated_values)
        for grouping_key, values in values_per_grouping_key.items():
            current_mode = mode
            if mode == 'mixed':
                current_mode = 'included'
                for base_line, taxes_data in values['base_line_x_taxes_data']:
                    if any(
                        not tax_data['price_include']
                        for tax_data in taxes_data
                        if (
                            not base_line['currency_id'].is_zero(tax_data['tax_amount_currency'])
                            or not company.currency_id.is_zero(tax_data['tax_amount'])
                        )
                    ):
                        current_mode = 'excluded'
                        break

            currency = grouping_key['currency']
            for delta_currency_indicator, delta_currency in (
                ('_currency', currency),
                ('', company.currency_id),
            ):
                if current_mode == 'excluded':
                    # Price-excluded rounding.
                    raw_total_excluded = values[f'target_total_excluded{delta_currency_indicator}']
                    if not raw_total_excluded:
                        continue

                    rounded_raw_total_excluded = delta_currency.round(raw_total_excluded)
                    total_excluded = values[f'total_excluded{delta_currency_indicator}']
                    delta_total_excluded = rounded_raw_total_excluded - total_excluded
                    target_factors = [
                        {
                            'factor': base_line['tax_details'][f'raw_total_excluded{delta_currency_indicator}'],
                            'base_line': base_line,
                        }
                        for base_line, _taxes_data in values['base_line_x_taxes_data']
                    ]
                else:
                    # Price-included rounding.
                    raw_total_included = (
                        values[f'target_total_excluded{delta_currency_indicator}']
                        + values[f'target_tax_amount{delta_currency_indicator}']
                    )
                    if not raw_total_included:
                        continue

                    rounded_raw_total_included = delta_currency.round(raw_total_included)
                    total_included = (
                        values[f'total_excluded{delta_currency_indicator}']
                        + values[f'tax_amount{delta_currency_indicator}']
                    )
                    delta_total_excluded = rounded_raw_total_included - total_included
                    target_factors = [
                        {
                            'factor': base_line['tax_details'][f'raw_total_included{delta_currency_indicator}'],
                            'base_line': base_line,
                        }
                        for base_line, _taxes_data in values['base_line_x_taxes_data']
                    ]

                amounts_to_distribute = self._distribute_delta_amount_smoothly(
                    precision_digits=delta_currency.decimal_places,
                    delta_amount=delta_total_excluded,
                    target_factors=target_factors,
                )
                for target_factor, amount_to_distribute in zip(target_factors, amounts_to_distribute):
                    base_line = target_factor['base_line']
                    base_line['tax_details'][f'delta_total_excluded{delta_currency_indicator}'] += amount_to_distribute