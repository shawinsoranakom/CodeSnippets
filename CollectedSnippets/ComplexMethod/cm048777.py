def _round_base_lines_tax_details(self, base_lines, company, tax_lines=None):
        """ Round the 'tax_details' added to base_lines with the '_add_accounting_data_to_base_line_tax_details'.
        This method performs all the rounding and take care of rounding issues that could appear when using the
        'round_globally' tax computation method, specially if some price included taxes are involved.

        This method copies all float prefixed with 'raw_' in the tax_details to the corresponding float without 'raw_'.
        In almost all countries, the round globally should be the tax computation method.
        When there is an EDI, we need the raw amounts to be reported with more decimals (usually 6 to 8).
        So if you need to report the price excluded amount for a single line, you need to use
        'raw_total_excluded_currency' / 'raw_total_excluded' instead of 'total_excluded_currency' / 'total_excluded' because
        the latest are rounded. In short, rounding yourself the amounts is probably a mistake and you are probably adding some
        rounding issues in your code.

        The rounding is made by aggregating the raw amounts per tax first.
        Then we round the total amount per tax, same for each tax amount in each base lines.
        Finally, we distribute the delta on each base lines.
        The delta is available in 'delta_total_excluded_currency' / 'delta_total_excluded' in each base line.

        Let's take an example using round globally.
        Suppose two lines:
        l1: price_unit = 21.53, tax = 21% incl
        l2: price_unit = 21.53, tax = 21% incl

        The raw_total_excluded is computed as 21.53 / 1.21 = 17.79338843
        The total_excluded is computed as round(17.79338843) = 17.79
        The total raw_base_amount for 21% incl is computed as 17.79338843 * 2 = 35.58677686
        The total base_amount for 21% incl is round(35.58677686) = 35.59
        The delta_base_amount is computed as 35.59 - 17.79 - 17.79 = 0.01 and will be added on l1.

        For the tax amounts:
        The raw_tax_amount is computed as 21.53 / 1.21 * 0.21 = 3.73661157
        The tax_amount is computed as round(3.73661157) = 3.74
        The total raw_tax_amount for 21% incl is computed as 3.73661157 * 2 = 7.473223141
        The total tax_amount for 21% incl is computed as round(7.473223141) = 7.47
        The delta amount for 21% incl is computed as 7.47 - 3.74 - 3.74 = -0.01 and will be added to the corresponding
        tax_data in l1.

        If l1 and l2 are invoice lines, the result will be:
        l1: price_unit = 21.53, tax = 21% incl, price_subtotal = 17.79, price_total = 21.53, balance = 17.80
        l2: price_unit = 21.53, tax = 21% incl, price_subtotal = 17.79, price_total = 21.53, balance = 17.79
        To compute the tax lines, we use the tax details in base_line['tax_details']['taxes_data'] that contain
        respectively 3.73 + 3.74 = 7.47.
        Since the untaxed amount of the invoice is computed based on the accounting balance:
        amount_untaxed = 17.80 + 17.79 = 35.59
        amount_tax = 7.47
        amount_total = 21.53 + 21.53 = 43.06

        The amounts are globally correct because 35.59 * 0.21 = 7.4739 ~= 7.47.

        [!] Mirror of the same method in account_tax.js.
        PLZ KEEP BOTH METHODS CONSISTENT WITH EACH OTHERS.

        :param base_lines:          A list of base lines generated using the '_prepare_base_line_for_taxes_computation' method.
        :param company:             The company owning the base lines.
        :param tax_lines:           A optional list of base lines generated using the '_prepare_tax_line_for_taxes_computation'
                                    method. If specified, the tax amounts will be computed based on those existing tax lines.
                                    It's used to keep the manual tax amounts set by the user.
        """
        # Raw rounding.
        for base_line in base_lines:
            tax_details = base_line['tax_details']

            for suffix, currency in (('_currency', base_line['currency_id']), ('', company.currency_id)):
                total_excluded_field = f'total_excluded{suffix}'
                tax_details[total_excluded_field] = currency.round(tax_details[f'raw_{total_excluded_field}'])

                for tax_data in tax_details['taxes_data']:
                    for prefix in ('base', 'tax'):
                        field = f'{prefix}_amount{suffix}'
                        tax_data[field] = currency.round(tax_data[f'raw_{field}'])

        # Apply 'manual_tax_amounts'.
        for base_line in base_lines:
            manual_tax_amounts = base_line['manual_tax_amounts']
            rate = base_line['rate']
            tax_details = base_line['tax_details']

            for suffix, currency in (('_currency', base_line['currency_id']), ('', company.currency_id)):
                total_field = f'total_excluded{suffix}'
                manual_field = f'manual_{total_field}'
                if base_line[manual_field] is not None:
                    tax_details[total_field] = base_line[manual_field]
                    if suffix == '_currency' and rate:
                        tax_details['total_excluded'] = company.currency_id.round(tax_details[total_field] / rate)

                for tax_data in tax_details['taxes_data']:
                    tax = tax_data['tax']
                    reverse_charge_sign = -1 if tax_data['is_reverse_charge'] else 1
                    current_manual_tax_amounts = manual_tax_amounts and manual_tax_amounts.get(str(tax.id)) or {}
                    for prefix, factor in (('base', 1), ('tax', reverse_charge_sign)):
                        field = f'{prefix}_amount{suffix}'
                        if field in current_manual_tax_amounts:
                            tax_data[field] = currency.round(factor * current_manual_tax_amounts[field])
                            if suffix == '_currency' and rate:
                                tax_data[f'{prefix}_amount'] = company.currency_id.round(tax_data[field] / rate)

        # Compute 'total_included' & add 'delta_total_excluded'.
        for base_line in base_lines:
            tax_details = base_line['tax_details']

            for suffix in ('_currency', ''):
                tax_details[f'delta_total_excluded{suffix}'] = 0.0
                tax_details[f'total_included{suffix}'] = tax_details[f'total_excluded{suffix}']

                for tax_data in tax_details['taxes_data']:
                    tax_details[f'total_included{suffix}'] += tax_data[f'tax_amount{suffix}']

        self._round_tax_details_tax_amounts(base_lines, company)
        self._round_tax_details_base_lines(base_lines, company)
        self._round_tax_details_tax_amounts_from_tax_lines(base_lines, company, tax_lines)