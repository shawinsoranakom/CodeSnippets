def _create_non_reconciliable_move_lines(self, data):
        # Create account.move.line records for
        #   - sales
        #   - taxes
        #   - stock expense
        #   - non-cash split receivables (not for automatic reconciliation)
        #   - non-cash combine receivables (not for automatic reconciliation)
        taxes = data.get('taxes')
        sales = data.get('sales')
        stock_expense = data.get('stock_expense')
        rounding_difference = data.get('rounding_difference')
        MoveLine = data.get('MoveLine')

        tax_vals = [self._get_tax_vals(key, amounts['amount'], amounts['amount_converted'], amounts['base_amount_converted']) for key, amounts in taxes.items()]
        # Check if all taxes lines have account_id assigned. If not, there are repartition lines of the tax that have no account_id.
        tax_names_no_account = [line['name'] for line in tax_vals if not line['account_id']]
        if tax_names_no_account:
            raise UserError(_(
                'Unable to close and validate the session.\n'
                'Please set corresponding tax account in each repartition line of the following taxes: \n%s',
                ', '.join(tax_names_no_account)
            ))
        rounding_vals = []

        if not float_is_zero(rounding_difference['amount'], precision_rounding=self.currency_id.rounding) or not float_is_zero(rounding_difference['amount_converted'], precision_rounding=self.currency_id.rounding):
            rounding_vals = [self._get_rounding_difference_vals(rounding_difference['amount'], rounding_difference['amount_converted'])]

        MoveLine.create(tax_vals)
        move_line_ids = MoveLine.create(list(starmap(self._get_sale_vals, sales.items())))
        for key, ml_id in zip(sales.keys(), move_line_ids.ids):
            sales[key]['move_line_id'] = ml_id
        MoveLine.create(
            [self._get_stock_expense_vals(key, amounts['amount'], amounts['amount_converted']) for key, amounts in stock_expense.items()]
            + rounding_vals
        )

        return data