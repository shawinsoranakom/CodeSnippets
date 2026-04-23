def _dispatch_taxes_into_new_base_lines(self, base_lines, company, exclude_function):
        """ Extract taxes from base lines and turn them into sub-base lines.

        [!] Mirror of the same method in account_tax.js.
        PLZ KEEP BOTH METHODS CONSISTENT WITH EACH OTHERS.

        :param base_lines:          A list of base lines generated using the '_prepare_base_line_for_taxes_computation' method.
        :param company:             The company of the base lines.
        :param exclude_function:    A function taking a base line and a tax_data as parameter and returning
                                    a boolean indicating if the tax_data has to be exclude or not.
        :return:                    The new base lines with some extra data that have been removed.
                                    The newly created base lines will be under the 'removed_taxes_data_base_lines' key.
        """
        def partition_function(base_line, tax_data):
            return not exclude_function(base_line, tax_data)

        base_lines_partition_taxes = self._partition_base_lines_taxes(base_lines, partition_function)[0]
        new_base_lines_list = [[] for _base_line in base_lines]
        to_process = [
            (index, base_line, taxes_to_exclude)
            for index, (base_line, taxes_to_keep, taxes_to_exclude) in enumerate(base_lines_partition_taxes)
        ]
        while to_process:
            index, base_line, taxes_to_exclude = to_process[0]
            to_process = to_process[1:]

            tax_details = base_line['tax_details']
            taxes_data = tax_details['taxes_data']

            # Get the index of the next 'tax_data' to exclude.
            next_split_index = None
            for i, tax_data in enumerate(taxes_data):
                if tax_data['tax'] in taxes_to_exclude:
                    next_split_index = i
                    break

            if next_split_index is None:
                new_base_lines_list[index].append(dict(base_line))
                continue

            common_taxes_data = taxes_data[:next_split_index]
            tax_data_to_remove = taxes_data[next_split_index]
            remaining_taxes_data = taxes_data[next_split_index + 1:]

            # Split 'tax_details'.
            first_tax_details = {
                k: tax_details[k]
                for k in (
                    'raw_total_excluded_currency',
                    'raw_total_excluded',
                    'total_excluded_currency',
                    'total_excluded',
                    'delta_total_excluded_currency',
                    'delta_total_excluded',
                )
            }
            first_tax_details['taxes_data'] = common_taxes_data
            first_tax_details['raw_total_included_currency'] = (
                first_tax_details['raw_total_excluded_currency']
                + sum(common_tax_data['raw_tax_amount_currency'] for common_tax_data in common_taxes_data)
            )
            first_tax_details['total_included_currency'] = (
                first_tax_details['total_excluded_currency']
                + first_tax_details['delta_total_excluded_currency']
                + sum(common_tax_data['tax_amount_currency'] for common_tax_data in common_taxes_data)
            )
            first_tax_details['raw_total_included'] = (
                first_tax_details['raw_total_excluded']
                + sum(common_tax_data['raw_tax_amount'] for common_tax_data in common_taxes_data)
            )
            first_tax_details['total_included'] = (
                first_tax_details['total_excluded']
                + first_tax_details['delta_total_excluded']
                + sum(common_tax_data['tax_amount'] for common_tax_data in common_taxes_data)
            )
            second_tax_details = {
                'raw_total_excluded_currency': tax_data_to_remove['raw_tax_amount_currency'],
                'raw_total_excluded': tax_data_to_remove['raw_tax_amount'],
                'total_excluded_currency': tax_data_to_remove['tax_amount_currency'],
                'total_excluded': tax_data_to_remove['tax_amount'],
                'delta_total_excluded_currency': 0.0,
                'delta_total_excluded': 0.0,
                'raw_total_included_currency': tax_data_to_remove['raw_tax_amount_currency'],
                'raw_total_included': tax_data_to_remove['raw_tax_amount'],
                'total_included_currency': tax_data_to_remove['tax_amount_currency'],
                'total_included': tax_data_to_remove['tax_amount'],
                'taxes_data': [],
            }

            target_factors = [
                {
                    'factor': first_tax_details['raw_total_excluded_currency'],
                    'tax_details': first_tax_details,
                },
                {
                    'factor': second_tax_details['raw_total_excluded_currency'],
                    'tax_details': second_tax_details,
                },
            ]
            for remaining_tax_data in remaining_taxes_data:
                if remaining_tax_data['tax'] in tax_data_to_remove['taxes']:
                    new_remaining_taxes_data = self._split_tax_data(base_line, remaining_tax_data, company, target_factors)

                    first_tax_data = new_remaining_taxes_data[0]

                    second_tax_details['taxes_data'].append(new_remaining_taxes_data[1])
                    second_tax_details['raw_total_included_currency'] += new_remaining_taxes_data[1]['raw_tax_amount_currency']
                    second_tax_details['raw_total_included'] += new_remaining_taxes_data[1]['raw_tax_amount']
                    second_tax_details['total_included_currency'] += new_remaining_taxes_data[1]['tax_amount_currency']
                    second_tax_details['total_included'] += new_remaining_taxes_data[1]['tax_amount']
                else:
                    first_tax_data = remaining_tax_data

                first_tax_details['taxes_data'].append(first_tax_data)
                first_tax_details['raw_total_included_currency'] += first_tax_data['raw_tax_amount_currency']
                first_tax_details['raw_total_included'] += first_tax_data['raw_tax_amount']
                first_tax_details['total_included_currency'] += first_tax_data['tax_amount_currency']
                first_tax_details['total_included'] += first_tax_data['tax_amount']

            # Split 'base_line'.
            first_taxes = self.env['account.tax']
            for tax_data in first_tax_details['taxes_data']:
                first_taxes += tax_data['tax']
            first_base_line = self._prepare_base_line_for_taxes_computation(
                base_line,
                tax_ids=first_taxes,
                tax_details=first_tax_details,
            )

            second_taxes = self.env['account.tax']
            for tax_data in second_tax_details['taxes_data']:
                second_taxes += tax_data['tax']
            second_base_line = self._prepare_base_line_for_taxes_computation(
                base_line,
                tax_ids=second_taxes,
                price_unit=(
                    second_tax_details['raw_total_excluded_currency']
                    + sum(
                        sub_tax_data['raw_tax_amount_currency']
                        for sub_tax_data in second_tax_details['taxes_data']
                        if sub_tax_data['tax'].price_include
                    )
                ) / (base_line['quantity'] or 1.0),
                tax_details=second_tax_details,
                _removed_tax_data=tax_data_to_remove,
            )
            to_process = [
                (index, first_base_line, taxes_to_exclude),
                (index, second_base_line, taxes_to_exclude),
            ] + to_process

        final_base_lines = []
        for new_base_lines in new_base_lines_list:
            new_base_lines[0]['removed_taxes_data_base_lines'] = new_base_lines[1:]
            final_base_lines.append(new_base_lines[0])
        return final_base_lines