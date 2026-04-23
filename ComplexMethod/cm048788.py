def _dispatch_global_discount_lines(self, base_lines, company):
        """ Dispatch the global discount lines present inside the base_lines passed as parameter across the others under the
        'discount_base_lines' key.

        [!] Only added python-side.

        :param base_lines:  A list of base lines generated using the '_prepare_base_line_for_taxes_computation' method.
        :param company:     The company owning the base lines.
        :return:            New base lines without any global discount but sub-lines added under the 'discount_base_lines' key.
        """
        # Dispatch lines.
        # First, we need to distinguish the mapping between the global discount lines and the others.
        # For now, we only dispatch base on taxes.
        new_base_lines = []
        discount_data_per_taxes = {}
        dispatched_neg_base_lines = []
        for base_line in base_lines:
            tax_details = base_line['tax_details']
            taxes_data = tax_details['taxes_data']

            # Get all the taxes flattened.
            taxes = self.env['account.tax']
            for gb_tax_data in taxes_data:
                taxes += gb_tax_data['tax']
            taxes = taxes.filtered(lambda tax: tax._can_be_discounted())

            discount_data = discount_data_per_taxes.setdefault(taxes, {
                'base_lines': [],
                'discount_base_lines': [],
            })

            new_base_line = {
                **base_line,
                'discount_base_lines': [],
            }

            if base_line['special_type'] == 'global_discount':
                discount_data['discount_base_lines'].append(new_base_line)
            else:
                discount_data['base_lines'].append(new_base_line)
            new_base_lines.append(new_base_line)

        # Split the discount base line accross the others.
        for discount_data in discount_data_per_taxes.values():
            discount_data['target_factors'] = [
                {
                    'base_line': base_line,
                    'factor': base_line['tax_details']['raw_total_excluded_currency'],
                }
                for base_line in discount_data['base_lines']
            ]
            if discount_data['target_factors']:
                dispatched_neg_base_lines += discount_data['discount_base_lines']
            else:
                continue

            for discount_base_line in discount_data['discount_base_lines']:
                splitted_base_lines = self._split_base_line(
                    base_line=discount_base_line,
                    company=company,
                    target_factors=discount_data['target_factors'],
                )
                for base_line, new_base_line in zip(discount_data['base_lines'], splitted_base_lines):
                    base_line['discount_base_lines'].append(new_base_line)
        return [x for x in new_base_lines if x not in dispatched_neg_base_lines]