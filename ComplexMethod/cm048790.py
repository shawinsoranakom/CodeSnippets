def _round_raw_total_excluded(
        self,
        base_lines,
        company,
        precision_digits=6,
        apply_strict_tolerance=False,
        in_foreign_currency=True,
    ):
        """ Round 'raw_total_excluded[_currency]' according 'precision_digits'.

        :param base_lines:              A list of python dictionaries created using the '_prepare_base_line_for_taxes_computation' method.
        :param company:                 The company owning the base lines.
        :param precision_digits:        The precision to be used to round.
        :param apply_strict_tolerance:  A flag ensuring a strict equality between rounded and raw amounts such as
                                            ROUND(SUM(raw_total_excluded FOREACH base_line), precision_digits)
                                            and SUM(total_excluded FOREACH base_line)
                                        If specified, the difference will be spread into the raw amounts to satisfy the equality.
        :param in_foreign_currency:     True if to be applied on amounts expressed in foreign currency,
                                        False for amounts expressed in company currency.
        """
        if not base_lines:
            return

        suffix_currency = base_lines[0]['currency_id'] if in_foreign_currency else company.currency_id
        suffix = '_currency' if in_foreign_currency else ''
        raw_field = f'raw_total_excluded{suffix}'

        for base_line in base_lines:
            tax_details = base_line['tax_details']
            tax_details[raw_field] = float_round(tax_details[raw_field], precision_digits=precision_digits)

        # Tolerance.
        if not apply_strict_tolerance:
            return

        def grouping_function(base_line, tax_data):
            return True

        base_lines_aggregated_values = self._aggregate_base_lines_tax_details(base_lines, grouping_function)
        values_per_grouping_key = self._aggregate_base_lines_aggregated_values(base_lines_aggregated_values)
        expected_total_excluded = sum(
            values[f'total_excluded{suffix}']
            for values in values_per_grouping_key.values()
        )
        current_raw_total_excluded = sum(
            base_line['tax_details'][raw_field]
            for base_line in base_lines
        )

        delta_raw_amount = self._get_delta_amount_to_reach_target(
            target_amount=expected_total_excluded,
            target_currency=suffix_currency,
            raw_current_amount=current_raw_total_excluded,
            raw_current_amount_precision_digits=precision_digits,
        )
        target_factors = [
            {
                'factor': base_line['tax_details'][raw_field],
                'base_line': base_line,
            }
            for base_line in base_lines
        ]
        amounts_to_distribute = self._distribute_delta_amount_smoothly(
            precision_digits=precision_digits,
            delta_amount=delta_raw_amount,
            target_factors=target_factors,
        )
        for target_factor, amount_to_distribute in zip(target_factors, amounts_to_distribute):
            base_line = target_factor['base_line']
            base_line['tax_details'][raw_field] += amount_to_distribute