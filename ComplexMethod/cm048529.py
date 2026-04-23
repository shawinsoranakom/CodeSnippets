def _get_move_dict_vals_change_account(self):
        line_vals = []

        # Group data from selected move lines
        counterpart_balances = defaultdict(lambda: defaultdict(lambda: 0))
        counterpart_distribution_amount = defaultdict(lambda: defaultdict(lambda: {}))
        grouped_source_lines = defaultdict(lambda: self.env['account.move.line'])

        for line in self.move_line_ids.filtered(lambda x: x.account_id != self.destination_account_id):
            counterpart_currency = line.currency_id
            counterpart_amount_currency = line.amount_currency

            if self.destination_account_id.currency_id and self.destination_account_id.currency_id != self.company_id.currency_id:
                counterpart_currency = self.destination_account_id.currency_id
                counterpart_amount_currency = self.company_id.currency_id._convert(line.balance, self.destination_account_id.currency_id, self.company_id, line.date)

            grouping_key = (line.partner_id, counterpart_currency)

            counterpart_balances[grouping_key]['amount_currency'] += counterpart_amount_currency
            counterpart_balances[grouping_key]['balance'] += line.balance
            if line.analytic_distribution:
                for account_id, distribution in line.analytic_distribution.items():
                    # For the counterpart, we will need to make a prorata of the different distribution of the lines
                    # This computes the total balance for each analytic account, for each counterpart line to generate
                    distribution_values = counterpart_distribution_amount[grouping_key]
                    distribution_values[account_id] = (line.balance * distribution + distribution_values.get(account_id, 0) * 100) / 100
            counterpart_balances[grouping_key]['analytic_distribution'] = counterpart_distribution_amount[grouping_key] or {}
            grouped_source_lines[(
                line.partner_id,
                line.currency_id,
                line.account_id,
                line.analytic_distribution and frozendict(line.analytic_distribution),
            )] += line

        # Generate counterpart lines' vals
        for (counterpart_partner, counterpart_currency), counterpart_vals in counterpart_balances.items():
            source_accounts = self.move_line_ids.mapped('account_id')
            counterpart_label = len(source_accounts) == 1 and _("Transfer from %s", source_accounts.display_name) or _("Transfer counterpart")

            # We divide the amount for each account by the total balance to reflect the lines counter-parted
            analytic_distribution = {
                account_id: (
                    100
                    if counterpart_currency.is_zero(counterpart_vals['balance'])
                    else 100 * distribution_amount / counterpart_vals['balance']
                )
                for account_id, distribution_amount in counterpart_vals['analytic_distribution'].items()
            }

            if not counterpart_currency.is_zero(counterpart_vals['amount_currency']) or not self.company_id.currency_id.is_zero(counterpart_vals['balance']):
                line_vals.append({
                    'name': counterpart_label,
                    'debit': counterpart_vals['balance'] > 0 and self.company_id.currency_id.round(counterpart_vals['balance']) or 0,
                    'credit': counterpart_vals['balance'] < 0 and self.company_id.currency_id.round(-counterpart_vals['balance']) or 0,
                    'account_id': self.destination_account_id.id,
                    'partner_id': counterpart_partner.id or None,
                    'amount_currency': counterpart_currency.round((counterpart_vals['balance'] < 0 and -1 or 1) * abs(counterpart_vals['amount_currency'])) or 0,
                    'currency_id': counterpart_currency.id,
                    'analytic_distribution': analytic_distribution,
                })

        # Generate change_account lines' vals
        for (partner, currency, account, analytic_distribution), lines in grouped_source_lines.items():
            account_balance = sum(line.balance for line in lines)
            if not self.company_id.currency_id.is_zero(account_balance):
                account_amount_currency = currency.round(sum(line.amount_currency for line in lines))
                line_vals.append({
                    'name': _('Transfer to %s', self.destination_account_id.display_name or _('[Not set]')),
                    'debit': account_balance < 0 and self.company_id.currency_id.round(-account_balance) or 0,
                    'credit': account_balance > 0 and self.company_id.currency_id.round(account_balance) or 0,
                    'account_id': account.id,
                    'partner_id': partner.id or None,
                    'currency_id': currency.id,
                    'amount_currency': (account_balance > 0 and -1 or 1) * abs(account_amount_currency),
                    'analytic_distribution': analytic_distribution,
                })

        # Get the lowest child company based on accounts used to avoid access error
        accounts = self.env['account.account'].browse([line['account_id'] for line in line_vals])
        companies = accounts.company_ids.filtered(lambda c: self.env.company in c.parent_ids) | self.env.company
        lowest_child_company = max(companies, key=lambda company: len(company.parent_ids))

        return [{
            'currency_id': self.journal_id.currency_id.id or self.journal_id.company_id.currency_id.id,
            'move_type': 'entry',
            'name': '/',
            'journal_id': self.journal_id.id,
            'company_id': lowest_child_company.id,
            'date': fields.Date.to_string(self.date),
            'ref': self.destination_account_id.display_name and _("Transfer entry to %s", self.destination_account_id.display_name or ''),
            'line_ids': [(0, 0, line) for line in line_vals],
        }]