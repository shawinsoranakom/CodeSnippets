def _prepare_invoice_aggregated_taxes(
        self,
        filter_invl_to_apply=None,
        filter_tax_values_to_apply=None,
        grouping_key_generator=None,
        round_from_tax_lines=None,
        postfix_function=None,
    ):
        """ This method is deprecated and will be removed in the next version.
        Use the following pattern instead:

        base_amls = self.line_ids.filtered(lambda x: x.display_type == 'product')
        base_lines = [self._prepare_product_base_line_for_taxes_computation(x) for x in base_amls]
        tax_amls = self.line_ids.filtered('tax_repartition_line_id')
        tax_lines = [self._prepare_tax_line_for_taxes_computation(x) for x in tax_amls]
        AccountTax._add_tax_details_in_base_lines(base_lines, self.company_id)
        AccountTax._round_base_lines_tax_details(base_lines, self.company_id, tax_lines=tax_lines)

        def grouping_function(base_line, tax_data):
            ...

        base_lines_aggregated_values = self._aggregate_base_lines_tax_details(base_lines, grouping_function)
        values_per_grouping_key = self._aggregate_base_lines_aggregated_values(base_lines_aggregated_values)
        """
        self.ensure_one()
        AccountTax = self.env['account.tax']
        if round_from_tax_lines is None:
            round_from_tax_lines = filter_tax_values_to_apply or filter_invl_to_apply

        base_amls = self.line_ids.filtered(lambda x: x.display_type == 'product' and (not filter_invl_to_apply or filter_invl_to_apply(x)))
        base_lines = [self._prepare_product_base_line_for_taxes_computation(x) for x in base_amls]
        tax_amls = self.line_ids.filtered('tax_repartition_line_id')
        tax_lines = self._prepare_tax_lines_for_taxes_computation(tax_amls, round_from_tax_lines)
        AccountTax._add_tax_details_in_base_lines(base_lines, self.company_id)
        if postfix_function:
            postfix_function(base_lines)
        AccountTax._round_base_lines_tax_details(base_lines, self.company_id, tax_lines=tax_lines)

        # Retro-compatibility with previous aggregator.
        results = {
            'base_amount_currency': 0.0,
            'base_amount': 0.0,
            'tax_amount_currency': 0.0,
            'tax_amount': 0.0,
            'tax_details_per_record': defaultdict(lambda: {
                'base_amount_currency': 0.0,
                'base_amount': 0.0,
                'tax_amount_currency': 0.0,
                'tax_amount': 0.0,
            }),
            'base_lines': base_lines,
        }

        def total_grouping_function(base_line, tax_data):
            if tax_data:
                return not filter_tax_values_to_apply or filter_tax_values_to_apply(base_line, tax_data)

        # Report the total amounts.
        base_lines_aggregated_values = AccountTax._aggregate_base_lines_tax_details(base_lines, total_grouping_function)
        for base_line, aggregated_values in base_lines_aggregated_values:
            record = base_line['record']
            base_line_results = results['tax_details_per_record'][record]
            base_line_results['base_line'] = base_line
            for grouping_key, values in aggregated_values.items():
                if grouping_key:
                    for key in ('base_amount', 'base_amount_currency', 'tax_amount', 'tax_amount_currency'):
                        base_line_results[key] += values[key]

        values_per_grouping_key = AccountTax._aggregate_base_lines_aggregated_values(base_lines_aggregated_values)
        for grouping_key, values in values_per_grouping_key.items():
            if grouping_key:
                for key in ('base_amount', 'base_amount_currency', 'tax_amount', 'tax_amount_currency'):
                    results[key] += values[key]

        # Same with the custom grouping_key passed as parameter.
        def tax_details_grouping_function(base_line, tax_data):
            if not total_grouping_function(base_line, tax_data):
                return None
            if grouping_key_generator:
                grouping_key = grouping_key_generator(base_line, tax_data)
                assert grouping_key is not None  # None must be kept for inner-grouping.
                return grouping_key
            return tax_data['tax']

        base_lines_aggregated_values = AccountTax._aggregate_base_lines_tax_details(base_lines, tax_details_grouping_function)
        for base_line, aggregated_values in base_lines_aggregated_values:
            record = base_line['record']
            base_line_results = results['tax_details_per_record'][record]
            base_line_results['tax_details'] = tax_details = {}
            for grouping_key, values in aggregated_values.items():
                if not grouping_key:
                    continue
                if isinstance(grouping_key, dict):
                    values.update(grouping_key)
                tax_details[grouping_key] = values

        values_per_grouping_key = AccountTax._aggregate_base_lines_aggregated_values(base_lines_aggregated_values)
        results['tax_details'] = tax_details = {}
        for grouping_key, values in values_per_grouping_key.items():
            if not grouping_key:
                continue
            if isinstance(grouping_key, dict):
                values.update(grouping_key)
            tax_details[grouping_key] = values

        return results