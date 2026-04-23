def _get_expenses_profitability_items(self, with_action=True):
        if not self.account_id:
            return {}
        can_see_expense = with_action and self.env.user.has_group('hr_expense.group_hr_expense_team_approver')

        expenses_read_group = self.env['hr.expense']._read_group(
            [
                ('state', 'in', ['posted', 'in_payment', 'paid']),
                ('analytic_distribution', 'in', self.account_id.ids),
            ],
            groupby=['currency_id'],
            aggregates=['id:array_agg', 'untaxed_amount_currency:sum'],
        )
        if not expenses_read_group:
            return {}
        expense_ids = []
        amount_billed = 0.0
        for currency, ids, untaxed_amount_currency_sum in expenses_read_group:
            if can_see_expense:
                expense_ids.extend(ids)
            amount_billed += currency._convert(
                from_amount=untaxed_amount_currency_sum,
                to_currency=self.currency_id,
                company=self.company_id,
            )

        section_id = 'expenses'
        expense_profitability_items = {
            'costs': {'id': section_id, 'sequence': self._get_profitability_sequence_per_invoice_type()[section_id], 'billed': -amount_billed, 'to_bill': 0.0},
        }
        if can_see_expense:
            args = [section_id, [('id', 'in', expense_ids)]]
            if len(expense_ids) == 1:
                args.append(expense_ids[0])
            action = {'name': 'action_profitability_items', 'type': 'object', 'args': json.dumps(args)}
            expense_profitability_items['costs']['action'] = action
        return expense_profitability_items