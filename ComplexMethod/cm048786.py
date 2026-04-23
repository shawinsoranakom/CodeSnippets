def _reduce_base_lines_to_target_amount(
        self,
        base_lines,
        company,
        amount_type,
        amount,
        computation_key=None,
        grouping_function=None,
        aggregate_function=None,
    ):
        """

        :param base_lines:          A list of base lines generated using the '_prepare_base_line_for_taxes_computation' method.
        :param company:             The company of the base lines.
        :param amount_type:         'fixed' or 'percent' indicating the type of the down payment.
        :param amount:              The amount of the down payment in case of 'fixed' amount_type. Otherwise, a percentage [0-100].
        :param computation_key:     The key that will be used to split the base lines to round the tax amounts.
        :param grouping_function:   An optional function taking a base line as parameter and returning a grouping key
                                    being the way the base lines will be aggregated all together.
                                    By default, the base lines will be aggregated by taxes.
        :param aggregate_function:  An optional function taking the 2 base lines as parameter to be aggregated together.
        :return:                    A new list of base lines having total amounts exactly matching the expected 'amount'/'amount_type'.
        """
        if not base_lines:
            return []

        currency = base_lines[0]['currency_id']
        rate = base_lines[0]['rate']

        # Compute the current total amount of the base lines.
        def grouping_function_total(base_line, tax_data):
            return True

        base_lines_aggregated_values = self._aggregate_base_lines_tax_details(base_lines, grouping_function_total)
        values_per_grouping_key = self._aggregate_base_lines_aggregated_values(base_lines_aggregated_values)
        total_amount_currency = sum(
            values['total_excluded_currency'] + values['tax_amount_currency']
            for _grouping_key, values in values_per_grouping_key.items()
        )
        total_amount = sum(
            values['total_excluded'] + values['tax_amount']
            for _grouping_key, values in values_per_grouping_key.items()
        )

        # Compute the current total tax amount per tax.
        def grouping_function_tax(base_line, tax_data):
            return str(tax_data['tax'].id) if tax_data else None

        base_lines_aggregated_values = self._aggregate_base_lines_tax_details(base_lines, grouping_function_tax)
        values_per_grouping_key = self._aggregate_base_lines_aggregated_values(base_lines_aggregated_values)
        tax_amounts_per_tax = {
            grouping_key: {
                'tax_amount_currency': values['tax_amount_currency'],
                'tax_amount': values['tax_amount'],
                'base_amount_currency': values['base_amount_currency'],
                'base_amount': values['base_amount'],
            }
            for grouping_key, values in values_per_grouping_key.items()
            if grouping_key
        }

        # Turn the 'amount_type' / 'amount' into a percentage and the total amounts to be reached
        # from the base lines.
        sign = -1 if amount < 0.0 else 1
        signed_amount = sign * amount
        if amount_type == 'fixed':
            percentage = (signed_amount / total_amount_currency) if total_amount_currency else 0.0
            expected_total_amount_currency = currency.round(amount)
            expected_total_amount = company.currency_id.round(expected_total_amount_currency / rate) if rate else 0.0
        else:  # if amount_type == 'percent':
            percentage = signed_amount / 100.0
            expected_total_amount_currency = currency.round(total_amount_currency * sign * percentage)
            expected_total_amount = company.currency_id.round(total_amount * sign * percentage)

        # Compute the expected amounts.
        expected_tax_amounts = {
            grouping_key: {
                'tax_amount_currency': currency.round(values['tax_amount_currency'] * sign * percentage),
                'tax_amount': company.currency_id.round(values['tax_amount'] * sign * percentage),
                'base_amount_currency': currency.round(values['base_amount_currency'] * sign * percentage),
                'base_amount': company.currency_id.round(values['base_amount'] * sign * percentage),
            }
            for grouping_key, values in tax_amounts_per_tax.items()
        }
        expected_base_amount_currency = expected_total_amount_currency - sum(
            values['tax_amount_currency']
            for values in expected_tax_amounts.values()
        )
        expected_base_amount = expected_total_amount - sum(
            values['tax_amount']
            for values in expected_tax_amounts.values()
        )

        # Reduce the base lines to minimize the number of lines.
        reduced_base_lines = self._reduce_base_lines_with_grouping_function(
            base_lines=base_lines,
            grouping_function=grouping_function,
            aggregate_function=aggregate_function,
            computation_key=computation_key,
        )
        if not reduced_base_lines:
            return []

        # Reduce the unit price to approach the target amount.
        new_base_lines = []
        for base_line in reduced_base_lines:
            new_base_lines.append(self._prepare_base_line_for_taxes_computation(
                base_line,
                price_unit=base_line['price_unit'] * sign * percentage,
                computation_key=computation_key,
            ))
        self._add_tax_details_in_base_lines(new_base_lines, company)
        self._round_base_lines_tax_details(new_base_lines, company)

        # Smooth distribution of the delta tax/base amounts.
        sorted_base_lines = sorted(
            new_base_lines,
            key=lambda base_line: (bool(base_line['special_type']), -base_line['tax_details']['total_excluded_currency'])
        )
        base_lines_aggregated_values = self._aggregate_base_lines_tax_details(new_base_lines, grouping_function_tax)
        values_per_grouping_key = self._aggregate_base_lines_aggregated_values(base_lines_aggregated_values)
        current_tax_amounts_per_tax = {
            grouping_key: {
                'tax_amount_currency': values['tax_amount_currency'],
                'tax_amount': values['tax_amount'],
                'base_amount_currency': values['base_amount_currency'],
                'base_amount': values['base_amount'],
            }
            for grouping_key, values in values_per_grouping_key.items()
            if grouping_key
        }
        for tax_id_str, tax_amounts in current_tax_amounts_per_tax.items():
            for delta_suffix, delta_tax_amount, delta_base_amount, delta_currency in (
                (
                    '_currency',
                    expected_tax_amounts[tax_id_str]['tax_amount_currency'] - tax_amounts['tax_amount_currency'],
                    expected_tax_amounts[tax_id_str]['base_amount_currency'] - tax_amounts['base_amount_currency'],
                    currency,
                ),
                (
                    '',
                    expected_tax_amounts[tax_id_str]['tax_amount'] - tax_amounts['tax_amount'],
                    expected_tax_amounts[tax_id_str]['base_amount'] - tax_amounts['base_amount'],
                    company.currency_id,
                ),
            ):
                # Tax amount.
                tax_amount_currency = tax_amounts['tax_amount_currency']
                if tax_amount_currency:
                    target_factors = [
                        {
                            'factor': abs(tax_data['tax_amount_currency'] / tax_amount_currency),
                            'base_line': base_line,
                            'tax_data': tax_data,
                        }
                        for base_line in sorted_base_lines
                        for tax_data in base_line['tax_details']['taxes_data']
                        if str(tax_data['tax'].id) == tax_id_str
                    ]
                    amounts_to_distribute = self._distribute_delta_amount_smoothly(
                        precision_digits=delta_currency.decimal_places,
                        delta_amount=delta_tax_amount,
                        target_factors=target_factors,
                    )
                    for target_factor, amount_to_distribute in zip(target_factors, amounts_to_distribute):
                        tax_data = target_factor['tax_data']
                        tax_data[f'tax_amount{delta_suffix}'] += amount_to_distribute

                # Base amount.
                base_amount_currency = tax_amounts['base_amount_currency']
                if base_amount_currency:
                    target_factors = [
                        {
                            'factor': abs(tax_data['base_amount_currency'] / base_amount_currency),
                            'base_line': base_line,
                            'tax_data': tax_data,
                        }
                        for base_line in sorted_base_lines
                        for tax_data in base_line['tax_details']['taxes_data']
                        if str(tax_data['tax'].id) == tax_id_str
                    ]
                    amounts_to_distribute = self._distribute_delta_amount_smoothly(
                        precision_digits=delta_currency.decimal_places,
                        delta_amount=delta_base_amount,
                        target_factors=target_factors,
                    )
                    for target_factor, amount_to_distribute in zip(target_factors, amounts_to_distribute):
                        tax_data = target_factor['tax_data']
                        tax_data[f'base_amount{delta_suffix}'] += amount_to_distribute

        base_lines_aggregated_values = self._aggregate_base_lines_tax_details(new_base_lines, grouping_function_total)
        values_per_grouping_key = self._aggregate_base_lines_aggregated_values(base_lines_aggregated_values)
        current_base_amount_currency = sum(
            values['total_excluded_currency']
            for _grouping_key, values in values_per_grouping_key.items()
        )
        current_base_amount = sum(
            values['total_excluded']
            for _grouping_key, values in values_per_grouping_key.items()
        )
        for delta_suffix, delta_base_amount, delta_currency in (
            ('_currency', expected_base_amount_currency - current_base_amount_currency, currency),
            ('', expected_base_amount - current_base_amount, company.currency_id),
        ):
            target_factors = [
                {
                    'factor': abs(
                        (base_line['tax_details']['total_excluded_currency'] + base_line['tax_details']['delta_total_excluded_currency'])
                        / current_base_amount_currency
                    ) if current_base_amount_currency else 0.0,
                    'base_line': base_line,
                }
                for base_line in sorted_base_lines
            ]
            amounts_to_distribute = self._distribute_delta_amount_smoothly(
                precision_digits=delta_currency.decimal_places,
                delta_amount=delta_base_amount,
                target_factors=target_factors,
            )
            for target_factor, amount_to_distribute in zip(target_factors, amounts_to_distribute):
                base_line = target_factor['base_line']
                tax_details = base_line['tax_details']
                tax_details[f'delta_total_excluded{delta_suffix}'] += amount_to_distribute
                if delta_suffix == '_currency':
                    base_line['price_unit'] += amount_to_distribute

        return new_base_lines