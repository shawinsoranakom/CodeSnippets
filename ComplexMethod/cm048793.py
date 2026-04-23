def _add_and_round_raw_gross_total_excluded_and_discount(
        self,
        base_lines,
        company,
        precision_digits=6,
        apply_strict_tolerance=False,
        in_foreign_currency=True,
        account_discount_base_lines=False,
    ):
        """ Compute and add 'raw_gross_total_excluded[_currency]' / 'raw_gross_price_unit[_currency]' / 'raw_discount_amount[_currency]'
        to the tax details according 'precision_digits' / 'in_foreign_currency'.

        :param base_lines:                  A list of python dictionaries created using the '_prepare_base_line_for_taxes_computation' method.
        :param company:                     The company owning the base lines.
        :param precision_digits:            The precision to be used to round.
        :param apply_strict_tolerance:      A flag ensuring a strict equality between rounded and raw amounts such as
                                                ROUND(SUM(raw_total_excluded + raw_discount_amount FOREACH base_line), precision_digits)
                                                and SUM(total_excluded FOREACH base_line) + ROUND(SUM(raw_discount_amount FOREACH base_line))
                                            If specified, the difference will be spread into the 'raw_gross_total_excluded' to satisfy the
                                            equality.
        :param in_foreign_currency:         True if to be applied on amounts expressed in foreign currency,
                                            False for amounts expressed in company currency.
        :param account_discount_base_lines: Account the distributed global discount in 'discount_base_lines'
                                            using '_dispatch_global_discount_lines' in 'raw_discount_amount'.
        """
        if not base_lines:
            return

        suffix_currency = base_lines[0]['currency_id'] if in_foreign_currency else company.currency_id
        suffix = '_currency' if in_foreign_currency else ''

        for base_line in base_lines:
            tax_details = base_line['tax_details']

            raw_gross_total_excluded = self._get_gross_total_without_tax(
                base_line=base_line,
                company=company,
                in_foreign_currency=in_foreign_currency,
                account_discount_base_lines=account_discount_base_lines,
                precision_digits=precision_digits,
            )
            tax_details[f'raw_gross_total_excluded{suffix}'] = raw_gross_total_excluded

            # Same as before but per unit.
            raw_gross_price_unit = self._get_price_unit_without_tax(
                base_line=base_line,
                company=company,
                raw_gross_total_excluded=raw_gross_total_excluded,
                in_foreign_currency=in_foreign_currency,
                precision_digits=precision_digits,
            )
            tax_details[f'raw_gross_price_unit{suffix}'] = raw_gross_price_unit

            # Compute the amount of the discount due to the 'discount' value set on 'base_line'.
            raw_discount_amount = self._get_discount_amount_without_tax(
                base_line=base_line,
                company=company,
                raw_gross_total_excluded=raw_gross_total_excluded,
                in_foreign_currency=in_foreign_currency,
                precision_digits=precision_digits,
            )
            tax_details[f'raw_discount_amount{suffix}'] = raw_discount_amount

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
        raw_total_discount_amount = sum(
            base_line['tax_details'][f'raw_discount_amount{suffix}']
            for values in values_per_grouping_key.values()
            for base_line, _taxes_data in values['base_line_x_taxes_data']
        )
        raw_total_gross_amount = sum(
            base_line['tax_details'][f'raw_gross_total_excluded{suffix}']
            for values in values_per_grouping_key.values()
            for base_line, _taxes_data in values['base_line_x_taxes_data']
        )
        total_discount_amount = suffix_currency.round(raw_total_discount_amount)
        expected_total_gross_amount = expected_total_excluded + total_discount_amount

        delta_raw_amount = self._get_delta_amount_to_reach_target(
            target_amount=expected_total_gross_amount,
            target_currency=suffix_currency,
            raw_current_amount=raw_total_gross_amount,
            raw_current_amount_precision_digits=precision_digits,
        )
        target_factors = [
            {
                'factor': base_line['tax_details'][f'raw_total_excluded{suffix}'],
                'base_line': base_line,
            }
            for values in values_per_grouping_key.values()
            for base_line, _taxes_data in values['base_line_x_taxes_data']
        ]
        amounts_to_distribute = self._distribute_delta_amount_smoothly(
            precision_digits=precision_digits,
            delta_amount=delta_raw_amount,
            target_factors=target_factors,
        )
        for target_factor, amount_to_distribute in zip(target_factors, amounts_to_distribute):
            base_line = target_factor['base_line']
            base_line['tax_details'][f'raw_gross_total_excluded{suffix}'] += amount_to_distribute