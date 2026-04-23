def _get_price_unit_without_tax(self, base_line, company, raw_gross_total_excluded, in_foreign_currency=True, precision_digits=None):
        """ Infer the gross price unit without tax from the base line.

        :param base_line:                   A base line (see '_prepare_base_line_for_taxes_computation').
        :param company:                     The company owning the base line.
        :param raw_gross_total_excluded:    The gross total without tax.
        :param in_foreign_currency:         True if to be applied on amounts expressed in foreign currency,
                                            False for amounts expressed in company currency.
        :param precision_digits:            The precision to be used to round.
        :return:                            The gross price unit without tax.
        """
        if (
            (precision_digits and float_is_zero(raw_gross_total_excluded, precision_digits=precision_digits))
            or not raw_gross_total_excluded
        ):
            if in_foreign_currency:
                raw_gross_price_unit = base_line['price_unit']
            elif base_line['rate']:
                raw_gross_price_unit = base_line['price_unit'] / base_line['rate']
            else:
                raw_gross_price_unit = 0.0
        elif not base_line['quantity']:
            raw_gross_price_unit = raw_gross_total_excluded
        else:
            raw_gross_price_unit = raw_gross_total_excluded / base_line['quantity']

        if precision_digits is not None:
            raw_gross_price_unit = float_round(raw_gross_price_unit, precision_digits=precision_digits)
        return raw_gross_price_unit