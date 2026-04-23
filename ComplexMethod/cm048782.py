def _merge_tax_details(self, tax_details_1, tax_details_2):
        """ Helper merging 2 tax details together coming from base lines.

        [!] Mirror of the same method in account_tax.js.
        PLZ KEEP BOTH METHODS CONSISTENT WITH EACH OTHERS.

        :param tax_details_1: First tax details.
        :param tax_details_2: Second tax details.
        :return: A new tax details combining the 2 passed as parameter.
        """
        results = {
            f'{prefix}{field}{suffix}': tax_details_1[f'{prefix}{field}{suffix}'] + tax_details_2[f'{prefix}{field}{suffix}']
            for prefix in ('raw_', '')
            for field in ('total_excluded', 'total_included')
            for suffix in ('_currency', '')
        }
        for suffix in ('_currency', ''):
            field = f'delta_total_excluded{suffix}'
            results[field] = tax_details_1[field] + tax_details_2[field]

        agg_taxes_data = {}
        for tax_details in (tax_details_1, tax_details_2):
            for tax_data in tax_details['taxes_data']:
                tax = tax_data['tax']
                if tax in agg_taxes_data:
                    agg_tax_data = agg_taxes_data[tax]
                    for prefix in ('raw_', ''):
                        for suffix in ('_currency', ''):
                            for field in ('base_amount', 'tax_amount'):
                                field_with_prefix = f'{prefix}{field}{suffix}'
                                agg_tax_data[field_with_prefix] += tax_data[field_with_prefix]
                else:
                    agg_taxes_data[tax] = dict(tax_data)
        results['taxes_data'] = list(agg_taxes_data.values())

        # In case there is some taxes that are in tax_details_1 but not on tax_details_2,
        # we have to shift manually the base amount. It happens with fixed taxes in which the base
        # is meaningless but still used in the computations.
        taxes_data_in_2 = {tax_data['tax'] for tax_data in tax_details_2['taxes_data']}
        not_discountable_taxes_data = {
            tax_data['tax']
            for tax_data in tax_details_1['taxes_data']
            if tax_data['tax'] not in taxes_data_in_2
        }
        for tax_data in results['taxes_data']:
            if tax_data['tax'] in not_discountable_taxes_data:
                for suffix in ('_currency', ''):
                    for prefix in ('raw_', ''):
                        tax_data[f'{prefix}base_amount{suffix}'] += tax_details_2[f'{prefix}total_excluded{suffix}']
                    tax_data[f'base_amount{suffix}'] += tax_details_2[f'delta_total_excluded{suffix}']

        return results