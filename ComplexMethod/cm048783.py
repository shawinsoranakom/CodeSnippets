def _split_tax_details(self, base_line, company, target_factors):
        """ Split the 'tax_details' in pieces according the factors passed as parameter.
        This method makes sure no amount is lost or gained during the process.

        [!] Mirror of the same method in account_tax.js.
        PLZ KEEP BOTH METHODS CONSISTENT WITH EACH OTHERS.

        :param base_line:       A base line.
        :param company:         The company owning the base lines.
        :param target_factors:  A list of dictionary containing at least 'factor' being the weight
                                defining how much delta will be allocated to this factor.
        :return                 A list of 'tax_details' having the same size as 'target_factors'.
        """
        currency = base_line['currency_id']
        tax_details = base_line['tax_details']

        factors = self._normalize_target_factors(target_factors)

        new_tax_details_list = []

        # Distribution of raw amounts.
        for _index, factor in factors:
            new_tax_details_list.append({
                'raw_total_excluded_currency': factor * tax_details['raw_total_excluded_currency'],
                'raw_total_excluded': factor * tax_details['raw_total_excluded'],
                'raw_total_included_currency': factor * tax_details['raw_total_included_currency'],
                'raw_total_included': factor * tax_details['raw_total_included'],
                'delta_total_excluded_currency': 0.0,
                'delta_total_excluded': 0.0,
                'taxes_data': [],
            })

        # Manage 'taxes_data'.
        for tax_data in tax_details['taxes_data']:
            new_taxes_data = self._split_tax_data(base_line, tax_data, company, target_factors)
            for new_tax_details, new_tax_data in zip(new_tax_details_list, new_taxes_data):
                new_tax_details['taxes_data'].append(new_tax_data)

        # Distribution of rounded amounts.
        for delta_currency_indicator, delta_currency in (
            ('_currency', currency),
            ('', company.currency_id),
        ):
            new_target_factors = [
                {
                    'factor': new_tax_details[f'raw_total_excluded{delta_currency_indicator}'],
                    'tax_details': new_tax_details,
                }
                for new_tax_details in new_tax_details_list
            ]
            field = f'total_excluded{delta_currency_indicator}'
            delta_amount = tax_details[field]
            amounts_to_distribute = self._distribute_delta_amount_smoothly(
                precision_digits=delta_currency.decimal_places,
                delta_amount=delta_amount,
                target_factors=new_target_factors,
            )
            for target_factor, amount_to_distribute in zip(new_target_factors, amounts_to_distribute):
                new_tax_details = target_factor['tax_details']
                new_tax_details[field] = amount_to_distribute

        # Manage 'total_included'.
        for new_tax_details in new_tax_details_list:
            for delta_currency_indicator in ('_currency', ''):
                new_tax_details[f'total_included{delta_currency_indicator}'] = (
                    new_tax_details[f'total_excluded{delta_currency_indicator}']
                    + sum(
                        new_tax_data[f'tax_amount{delta_currency_indicator}']
                        for new_tax_data in new_tax_details['taxes_data']
                    )
                )
        return new_tax_details_list