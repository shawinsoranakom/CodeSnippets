def _round_tax_details_tax_amounts(self, base_lines, company, mode='mixed'):
        """ Dispatch the delta in term of tax amounts across the tax details when dealing with the 'round_globally' method.
        Suppose 2 lines:
        - quantity=12.12, price_unit=12.12, tax=23%
        - quantity=12.12, price_unit=12.12, tax=23%
        The tax of each line is computed as round(12.12 * 12.12 * 0.23) = 33.79
        The expected tax amount of the whole document is round(12.12 * 12.12 * 0.23 * 2) = 67.57
        The delta in term of tax amount is 67.57 - 33.79 - 33.79 = -0.01

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
            if not tax_data:
                return
            return {
                'tax': tax_data['tax'],
                'currency': base_line['currency_id'],
                'is_refund': base_line['is_refund'],
                'is_reverse_charge': tax_data['is_reverse_charge'],
                'price_include': tax_data['price_include'],
                'computation_key': base_line['computation_key'],
            }

        base_lines_aggregated_values = self._aggregate_base_lines_tax_details(base_lines, grouping_function)
        values_per_grouping_key = self._aggregate_base_lines_aggregated_values(base_lines_aggregated_values)
        for grouping_key, values in values_per_grouping_key.items():
            if not grouping_key:
                continue

            price_include = grouping_key['price_include']
            currency = grouping_key['currency']
            for delta_currency_indicator, delta_currency in (
                ('_currency', currency),
                ('', company.currency_id),
            ):
                # Tax amount.
                raw_total_tax_amount = values[f'target_tax_amount{delta_currency_indicator}']
                rounded_raw_total_tax_amount = delta_currency.round(raw_total_tax_amount)
                total_tax_amount = values[f'tax_amount{delta_currency_indicator}']
                delta_total_tax_amount = rounded_raw_total_tax_amount - total_tax_amount

                if not delta_currency.is_zero(delta_total_tax_amount):
                    target_factors = [
                        {
                            'factor': tax_data[f'raw_tax_amount{delta_currency_indicator}'],
                            'tax_data': tax_data,
                        }
                        for _base_line, taxes_data in values['base_line_x_taxes_data']
                        for tax_data in taxes_data
                    ]
                    amounts_to_distribute = self._distribute_delta_amount_smoothly(
                        precision_digits=delta_currency.decimal_places,
                        delta_amount=delta_total_tax_amount,
                        target_factors=target_factors,
                    )
                    for target_factor, amount_to_distribute in zip(target_factors, amounts_to_distribute):
                        tax_data = target_factor['tax_data']
                        tax_data[f'tax_amount{delta_currency_indicator}'] += amount_to_distribute

                # Base amount.
                raw_total_base_amount = values[f'target_base_amount{delta_currency_indicator}']
                if (mode == 'mixed' and price_include) or mode == 'included':
                    raw_total_amount = raw_total_base_amount + raw_total_tax_amount
                    rounded_raw_total_amount = delta_currency.round(raw_total_amount)
                    total_amount = values[f'base_amount{delta_currency_indicator}'] + total_tax_amount + delta_total_tax_amount
                    delta_total_base_amount = rounded_raw_total_amount - total_amount
                elif (mode == 'mixed' and not price_include) or mode == 'excluded':
                    rounded_raw_total_base_amount = delta_currency.round(raw_total_base_amount)
                    total_base_amount = values[f'base_amount{delta_currency_indicator}']
                    delta_total_base_amount = rounded_raw_total_base_amount - total_base_amount

                if not delta_currency.is_zero(delta_total_base_amount):
                    target_factors = [
                        {
                            'factor': tax_data[f'raw_base_amount{delta_currency_indicator}'],
                            'tax_data': tax_data,
                        }
                        for _base_line, taxes_data in values['base_line_x_taxes_data']
                        for tax_data in taxes_data
                    ]
                    amounts_to_distribute = self._distribute_delta_amount_smoothly(
                        precision_digits=delta_currency.decimal_places,
                        delta_amount=delta_total_base_amount,
                        target_factors=target_factors,
                    )
                    for target_factor, amount_to_distribute in zip(target_factors, amounts_to_distribute):
                        tax_data = target_factor['tax_data']
                        tax_data[f'base_amount{delta_currency_indicator}'] += amount_to_distribute