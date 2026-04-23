def _reduce_base_lines_with_grouping_function(self, base_lines, grouping_function=None, aggregate_function=None, computation_key=None):
        """ Create the new base lines that will get the discount.
        Since they no longer contain fixed taxes, we can remove the quantity and aggregate them depending on
        the grouping_function passed as parameter.

        [!] Mirror of the same method in account_tax.js.
        PLZ KEEP BOTH METHODS CONSISTENT WITH EACH OTHERS.

        :param base_lines:          The base lines to be aggregated.
        :param grouping_function:   An optional function taking a base line as parameter and returning a grouping key
                                    being the way the base lines will be aggregated all together.
                                    By default, the base lines will be aggregated by taxes.
        :param aggregate_function:  An optional function taking the 2 base lines as parameter to be aggregated together.
        :param computation_key:     The computation_key to be set on the aggregated base_lines.
        :return:                    The base lines aggregated.
        """
        aggregated_base_lines = {}
        base_line_map = {}
        for base_line in base_lines:
            price_unit_after_discount = base_line['price_unit'] * (1 - (base_line['discount'] / 100.0))
            new_base_line = self._prepare_base_line_for_taxes_computation(
                base_line,
                price_unit=base_line['quantity'] * price_unit_after_discount,
                quantity=1.0,
                discount=0.0,
            )
            grouping_key = {'tax_ids': new_base_line['tax_ids']}
            if grouping_function:
                grouping_key.update(grouping_function(new_base_line))
            grouping_key = frozendict(grouping_key)

            if base_line['analytic_distribution']:
                for account_id, distribution in base_line['analytic_distribution'].items():
                    aggregated_base_lines.setdefault(account_id, []).append(distribution)

            target_base_line = base_line_map.get(grouping_key)
            if target_base_line:
                target_base_line['price_unit'] += new_base_line['price_unit']
                target_base_line['tax_details'] = self._merge_tax_details(
                    tax_details_1=target_base_line['tax_details'],
                    tax_details_2=base_line['tax_details'],
                )
                if aggregate_function:
                    aggregate_function(target_base_line, base_line)
            else:
                target_base_line = self._prepare_base_line_for_taxes_computation(
                    new_base_line,
                    **grouping_key,
                    computation_key=computation_key,
                    tax_details={
                        **base_line['tax_details'],
                        'taxes_data': [dict(tax_data) for tax_data in base_line['tax_details']['taxes_data']],
                    },
                )
                base_line_map[grouping_key] = target_base_line
                if aggregate_function:
                    aggregate_function(target_base_line, base_line)
            aggregated_base_lines.setdefault(grouping_key, []).append(base_line)

        # Remove zero lines.
        base_line_map = {
            grouping_key: base_line
            for grouping_key, base_line in base_line_map.items()
            if not base_line['currency_id'].is_zero(base_line['price_unit'])
        }

        # Compute the analytic distribution for the new base line.
        # To do so, we have to aggregate the analytic distribution of each line that has been aggregated.
        # We need to take care about the negative lines but also of the negative distribution.
        # Suppose:
        # - line1 of 1000 having an analytic distribution of 100%
        # - line2 of -100 having an analytic distribution of 50%
        # After the aggregation, the result will be an analytic distribution of
        # ((1000 * 1) + (-100 * 0.5)) / (1000 - 100) = 1.055555556
        for grouping_key, base_line in base_line_map.items():
            total_factor = 0.0
            analytic_distribution_to_aggregate = defaultdict(float)
            for aggregated_base_line in aggregated_base_lines[grouping_key]:
                amount = aggregated_base_line['tax_details']['raw_total_excluded_currency']
                total_factor += amount
                for account_id, distribution in (aggregated_base_line['analytic_distribution'] or {}).items():
                    analytic_distribution_to_aggregate[account_id] += distribution * amount / 100.0
            analytic_distribution = {}
            for account_id, amount in analytic_distribution_to_aggregate.items():
                analytic_distribution[account_id] = amount * 100 / total_factor
            base_line['analytic_distribution'] = analytic_distribution

        return list(base_line_map.values())