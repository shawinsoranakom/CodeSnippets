def _turn_base_line_is_refund_flag_off(self, base_line):
        """ Reverse the sign of the quantity plus all data in tax details.

        [!] Only added python-side.

        :param base_line: The base_line.
        :return: The base_line that is no longer a refund line.
        """
        if not base_line['is_refund']:
            return base_line

        new_base_line = {
            **base_line,
            'quantity': -base_line['quantity'],
            'is_refund': False,
        }
        tax_details = new_base_line['tax_details']
        new_tax_details = new_base_line['tax_details'] = {
            f'{prefix}{field}{suffix}': -tax_details[f'{prefix}{field}{suffix}']
            for prefix in ('raw_', '')
            for field in ('total_excluded', 'total_included')
            for suffix in ('_currency', '')
        }
        for suffix in ('_currency', ''):
            field = f'delta_total_excluded{suffix}'
            new_tax_details[field] = -tax_details[field]

        new_tax_details['taxes_data'] = new_taxes_data = []
        for tax_data in tax_details['taxes_data']:
            new_tax_data = {**tax_data}
            for prefix in ('raw_', ''):
                for suffix in ('_currency', ''):
                    for field in ('base_amount', 'tax_amount'):
                        field = f'{prefix}{field}{suffix}'
                        new_tax_data[field] = -tax_data[field]
            new_taxes_data.append(new_tax_data)

        return new_base_line