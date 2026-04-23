def _round_raw_tax_amounts(
        self,
        base_lines_aggregated_values,
        company,
        precision_digits=6,
        apply_strict_tolerance=False,
        in_foreign_currency=True,
    ):
        """ Round 'raw_tax_amount[_currency]'/'raw_base_amount[_currency]' according 'precision_digits' / 'in_foreign_currency'.

        :param base_lines_aggregated_values:    The result of '_aggregate_base_lines_tax_details'.
        :param company:                         The company owning the base lines.
        :param precision_digits:                The precision to be used to round.
        :param apply_strict_tolerance:          A flag ensuring a strict equality between rounded and raw amounts such as
                                                    ROUND(SUM(raw_tax_amount FOREACH base_line), precision_digits)
                                                    and SUM(tax_amount FOREACH base_line)
                                                If specified, the difference will be spread into the raw amounts to satisfy the equality.
                                                Regarding the base amounts, we keep a consistency between the tax rate between
                                                each raw_base_amount and raw_tax_amount but also globally with rounded amounts.
        :param in_foreign_currency:             True if to be applied on amounts expressed in foreign currency,
                                                False for amounts expressed in company currency.
        """
        if not base_lines_aggregated_values:
            return

        suffix_currency = base_lines_aggregated_values[0][0]['currency_id'] if in_foreign_currency else company.currency_id
        suffix = '_currency' if in_foreign_currency else ''

        for _base_line, aggregated_values in base_lines_aggregated_values:
            for values in aggregated_values.values():
                values[f'raw_tax_amount{suffix}'] = float_round(values[f'raw_tax_amount{suffix}'], precision_digits=precision_digits)
                values[f'raw_base_amount{suffix}'] = float_round(values[f'raw_base_amount{suffix}'], precision_digits=precision_digits)

        # Tolerance.
        if not apply_strict_tolerance:
            return

        tax_field = f'tax_amount{suffix}'
        raw_tax_field = f'raw_{tax_field}'
        base_field = f'base_amount{suffix}'
        raw_base_field = f'raw_{base_field}'
        values_per_grouping_key = self._aggregate_base_lines_aggregated_values(base_lines_aggregated_values)
        for grouping_key, values in values_per_grouping_key.items():
            tax_rate = (values[raw_tax_field] / values[raw_base_field]) if values[raw_base_field] else 0.0

            target_factors = [
                {
                    'factor': aggregated_values[grouping_key][raw_tax_field],
                    'aggregated_values': aggregated_values[grouping_key],
                }
                for base_line, aggregated_values in base_lines_aggregated_values
                if grouping_key in aggregated_values
            ]

            # Tax amount.
            expected_tax_amount = values[tax_field]
            current_raw_tax_amount = values[raw_tax_field]
            delta_raw_amount = self._get_delta_amount_to_reach_target(
                target_amount=expected_tax_amount,
                target_currency=suffix_currency,
                raw_current_amount=current_raw_tax_amount,
                raw_current_amount_precision_digits=precision_digits,
            )
            amounts_to_distribute = self._distribute_delta_amount_smoothly(
                precision_digits=precision_digits,
                delta_amount=delta_raw_amount,
                target_factors=target_factors,
            )
            for target_factor, amount_to_distribute in zip(target_factors, amounts_to_distribute):
                aggregated_values = target_factor['aggregated_values']
                aggregated_values[raw_tax_field] += amount_to_distribute
                values[raw_tax_field] += amount_to_distribute
                if amount_to_distribute and tax_rate:
                    new_raw_base_amount = aggregated_values[raw_tax_field] / tax_rate
                    rounded_new_raw_base_amount = float_round(new_raw_base_amount, precision_digits=precision_digits)
                    values[raw_base_field] += rounded_new_raw_base_amount - aggregated_values[raw_base_field]
                    aggregated_values[raw_base_field] = rounded_new_raw_base_amount

            # Base amount.
            if tax_rate:
                current_tax_raw_base_amount = (current_raw_tax_amount + delta_raw_amount) / tax_rate
                delta_raw_amount = self._get_delta_amount_to_reach_target(
                    target_amount=current_tax_raw_base_amount,
                    target_currency=suffix_currency,
                    raw_current_amount=values[raw_base_field],
                    raw_current_amount_precision_digits=precision_digits,
                )
                amounts_to_distribute = self._distribute_delta_amount_smoothly(
                    precision_digits=precision_digits,
                    delta_amount=delta_raw_amount,
                    target_factors=target_factors,
                )
                for target_factor, amount_to_distribute in zip(target_factors, amounts_to_distribute):
                    aggregated_values = target_factor['aggregated_values']
                    aggregated_values[raw_base_field] += amount_to_distribute
                    values[raw_base_field] += amount_to_distribute