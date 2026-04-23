def _reverse_quantity_base_line_extra_tax_data(self, extra_tax_data):
        """ Reverse all sign in extra_tax_data using the quantity.

        [!] Only added python-side.

        :param extra_tax_data: The manual taxes data stored on records.
        :return: The extra_tax_data but reversed.
        """
        if not extra_tax_data:
            return None

        new_extra_tax_data = copy.deepcopy(extra_tax_data)
        for field in ('quantity', 'manual_total_excluded_currency', 'manual_total_excluded'):
            if new_extra_tax_data.get(field):
                new_extra_tax_data[field] *= -1
        if new_extra_tax_data.get('manual_tax_amounts'):
            for current_manual_tax_amounts in new_extra_tax_data['manual_tax_amounts'].values():
                for suffix in ('_currency', ''):
                    for prefix in ('base', 'tax'):
                        field = f'{prefix}_amount{suffix}'
                        if current_manual_tax_amounts.get(field):
                            current_manual_tax_amounts[field] *= -1
        return new_extra_tax_data