def _round_tax_details_tax_amounts_from_tax_lines(self, base_lines, company, tax_lines):
        """ If tax lines are provided, the totals will be aggregated according them.
        At this point, everything is rounded and won't change anymore.

        [!] Only added python-side.

        :param base_lines:          A list of base lines generated using the '_prepare_base_line_for_taxes_computation' method.
        :param company:             The company owning the base lines.
        :param tax_lines:           A optional list of base lines generated using the '_prepare_tax_line_for_taxes_computation'
                                    method. If specified, the tax amounts will be computed based on those existing tax lines.
                                    It's used to keep the manual tax amounts set by the user.
        """
        if not tax_lines:
            return

        total_per_tax_line_key = defaultdict(lambda: {
            'currency': None,
            'tax_amount_currency': 0.0,
            'tax_amount': 0.0,
        })
        for tax_line in tax_lines:
            tax_rep = tax_line['tax_repartition_line_id']
            sign = tax_line['sign']
            tax = tax_rep.tax_id
            currency = tax_line['currency_id']
            tax_line_key = (tax.id, currency.id, tax_rep.document_type == 'refund')
            total_per_tax_line_key[tax_line_key]['currency'] = currency
            total_per_tax_line_key[tax_line_key]['tax_amount_currency'] += sign * tax_line['amount_currency']
            total_per_tax_line_key[tax_line_key]['tax_amount'] += sign * tax_line['balance']

        def grouping_function(base_line, tax_data):
            if not tax_data:
                return
            return {
                'tax': tax_data['tax'],
                'currency': base_line['currency_id'],
                'is_refund': base_line['is_refund'],
            }

        base_lines_aggregated_values = self._aggregate_base_lines_tax_details(base_lines, grouping_function)
        values_per_grouping_key = self._aggregate_base_lines_aggregated_values(base_lines_aggregated_values)
        for grouping_key, values in values_per_grouping_key.items():
            if not grouping_key:
                continue

            currency = grouping_key['currency']
            tax_line_key = (grouping_key['tax'].id, currency.id, grouping_key['is_refund'])
            if tax_line_key not in total_per_tax_line_key:
                continue

            for delta_currency_indicator, delta_currency in (
                ('_currency', currency),
                ('', company.currency_id),
            ):
                current_total_tax_amount = values[f'tax_amount{delta_currency_indicator}']
                if not current_total_tax_amount:
                    continue

                target_total_tax_amount = total_per_tax_line_key[tax_line_key][f'tax_amount{delta_currency_indicator}']
                delta_total_tax_amount = target_total_tax_amount - current_total_tax_amount

                target_factors = [
                    {
                        'factor': tax_data[f'tax_amount{delta_currency_indicator}'],
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