def _compute_currency_rate(self):
        """
            We want the default odoo rate when the following change:
            - the currency of the expense
            - the total amount in foreign currency
            - the date of the expense
            this will cause the rate to be recomputed twice with possible changes but we don't have the required fields
            to store the override state in stable
        """
        date_today = fields.Date.context_today(self)
        for expense in self:
            if expense.is_multiple_currency:
                if (
                        expense.currency_id != expense._origin.currency_id
                        or expense.total_amount_currency != expense._origin.total_amount_currency
                        or expense.date != expense._origin.date
                ):
                    expense._set_expense_currency_rate(date_today=date_today)
                else:
                    expense.currency_rate = expense.total_amount / expense.total_amount_currency if expense.total_amount_currency else 1.0
            else:  # Mono-currency case computation shortcut, no need for the label if there is no conversion
                expense.currency_rate = 1.0
                expense.label_currency_rate = False
                continue

            company_currency = expense.company_currency_id or expense.env.company.currency_id
            expense.label_currency_rate = _(
                '1 %(exp_cur)s = %(rate)s %(comp_cur)s',
                exp_cur=(expense.currency_id or company_currency).name,
                rate=float_repr(expense.currency_rate, 6),
                comp_cur=company_currency.name,
            )