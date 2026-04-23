def _get_invoice_counterpart_amls_for_early_payment_discount(self, aml_values_list, open_balance):
        """ Helper to get the values to create the counterpart journal items on the register payment wizard and the
        bank reconciliation widget in case of an early payment discount by taking care of the payment term lines we
        are matching and the exchange difference in case of multi-currencies.

        :param aml_values_list: A list of dictionaries containing:
            * aml:              The payment term line we match.
            * amount_currency:  The matched amount_currency for this line.
            * balance:          The matched balance for this line (could be different in case of multi-currencies).
        :param open_balance:    The current open balance to be covered by the early payment discount.
        :return: A list of values to create the counterpart journal items split in 3 categories:
            * term_lines:       The journal items containing the discount amounts for each receivable line when the
                                discount computation is excluded / mixed.
            * tax_lines:        The journal items acting as tax lines when the discount computation is included.
            * base_lines:       The journal items acting as base for tax lines when the discount computation is included.
            * exchange_lines:   The journal items representing the exchange differences in case of multi-currencies.
        """
        res = {
            'base_lines': {},
            'tax_lines': {},
            'term_lines': {},
            'exchange_lines': {},
        }

        res_per_invoice = {}
        for aml_values in aml_values_list:
            aml = aml_values['aml']
            invoice = aml.move_id

            if invoice not in res_per_invoice:
                res_per_invoice[invoice] = invoice._get_invoice_counterpart_amls_for_early_payment_discount_per_payment_term_line()

            for key in ('base_lines', 'tax_lines', 'term_lines'):
                for grouping_dict, vals in res_per_invoice[invoice][key][aml].items():
                    line_vals = res[key].setdefault(grouping_dict, {
                        **vals,
                        'amount_currency': 0.0,
                        'balance': 0.0,
                    })
                    line_vals['amount_currency'] += vals['amount_currency']
                    line_vals['balance'] += vals['balance']

                    # Track the balance to handle the exchange difference.
                    open_balance -= vals['balance']

        exchange_diff_sign = aml.company_currency_id.compare_amounts(open_balance, 0.0)
        if exchange_diff_sign != 0.0:

            if exchange_diff_sign > 0.0:
                exchange_line_account = aml.company_id.expense_currency_exchange_account_id
            else:
                exchange_line_account = aml.company_id.income_currency_exchange_account_id

            grouping_dict = {
                'account_id': exchange_line_account.id,
                'currency_id': aml.currency_id.id,
                'partner_id': aml.partner_id.id,
            }
            line_vals = res['exchange_lines'].setdefault(frozendict(grouping_dict), {
                **grouping_dict,
                'name': _("Early Payment Discount (Exchange Difference)"),
                'amount_currency': 0.0,
                'balance': 0.0,
            })
            line_vals['balance'] += open_balance

        return {
            key: [
                {
                    **grouping_dict,
                    **vals,
                }
                for grouping_dict, vals in mapping.items()
            ]
            for key, mapping in res.items()
        }