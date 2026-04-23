def _compute_debit_credit_balance(self):
        def convert(amount, from_currency):
            return from_currency._convert(
                from_amount=amount,
                to_currency=self.env.company.currency_id,
                company=self.env.company,
                date=fields.Date.today(),
            )

        domain = [('company_id', 'in', [False] + self.env.companies.ids)]
        if self.env.context.get('from_date', False):
            domain.append(('date', '>=', self.env.context['from_date']))
        if self.env.context.get('to_date', False):
            domain.append(('date', '<=', self.env.context['to_date']))

        for plan, accounts in self.grouped('plan_id').items():
            if not plan:
                accounts.debit = accounts.credit = accounts.balance = 0
                continue
            credit_groups = self.env['account.analytic.line']._read_group(
                domain=domain + [(plan._column_name(), 'in', self.ids), ('amount', '>=', 0.0)],
                groupby=[plan._column_name(), 'currency_id'],
                aggregates=['amount:sum'],
            )
            data_credit = defaultdict(float)
            for account, currency, amount_sum in credit_groups:
                data_credit[account.id] += convert(amount_sum, currency)

            debit_groups = self.env['account.analytic.line']._read_group(
                domain=domain + [(plan._column_name(), 'in', self.ids), ('amount', '<', 0.0)],
                groupby=[plan._column_name(), 'currency_id'],
                aggregates=['amount:sum'],
            )
            data_debit = defaultdict(float)
            for account, currency, amount_sum in debit_groups:
                data_debit[account.id] += convert(amount_sum, currency)

            for account in accounts:
                account.debit = -data_debit.get(account.id, 0.0)
                account.credit = data_credit.get(account.id, 0.0)
                account.balance = account.credit - account.debit