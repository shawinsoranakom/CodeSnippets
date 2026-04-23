def _get_gross_total_without_tax(self, base_line, company, in_foreign_currency=True, account_discount_base_lines=False, precision_digits=None):
        """ Infer the gross total without tax from the base line.

        :param base_line:                   A base line (see '_prepare_base_line_for_taxes_computation').
        :param company:                     The company owning the base line.
        :param in_foreign_currency:         True if to be applied on amounts expressed in foreign currency,
                                            False for amounts expressed in company currency.
        :param account_discount_base_lines: Account the distributed global discount in 'discount_base_lines'
                                            using '_dispatch_global_discount_lines' in 'raw_discount_amount'.
        :param precision_digits:            The precision to be used to round.
        :return:                            The gross total without tax.
        """
        suffix = '_currency' if in_foreign_currency else ''

        tax_details = base_line['tax_details']
        raw_total_excluded = tax_details[f'raw_total_excluded{suffix}']

        discount_factor = 1 - (base_line['discount'] / 100.0)
        if discount_factor:
            raw_gross_total_excluded = raw_total_excluded / discount_factor
        elif in_foreign_currency:
            raw_gross_total_excluded = base_line['price_unit'] * base_line['quantity']
        elif base_line['rate']:
            raw_gross_total_excluded = base_line['price_unit'] * base_line['quantity'] / base_line['rate']
        else:
            raw_gross_total_excluded = 0.0
        if account_discount_base_lines:
            raw_gross_total_excluded -= sum(
                discount_base_line['tax_details'][f'raw_total_excluded{suffix}']
                for discount_base_line in base_line.get('discount_base_lines', [])
            )

        if precision_digits is not None:
            raw_gross_total_excluded = float_round(raw_gross_total_excluded, precision_digits=precision_digits)
        return raw_gross_total_excluded