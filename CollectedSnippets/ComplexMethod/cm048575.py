def _create_default_account(self, company, journal_type, vals):
        # Don't get the digits on 'chart_template' since the chart template could be a custom one.
        random_account = self.env['account.account'].with_company(company).search(
            self.env['account.account']._check_company_domain(company),
            limit=1,
        )
        digits = len(random_account.code) if random_account else 6

        if journal_type in ('bank', 'credit'):
            account_prefix = company.bank_account_code_prefix or ''
        elif journal_type == 'cash':
            account_prefix = company.cash_account_code_prefix or company.bank_account_code_prefix or ''
        else:
            account_prefix = ''

        start_code = account_prefix.ljust(digits, '0')
        default_account_code = self.env['account.account'].with_company(company)._search_new_account_code(start_code)

        if journal_type in ('bank', 'cash'):
            default_account_vals = self._prepare_liquidity_account_vals(company, default_account_code, vals)
        elif journal_type == 'credit':
            default_account_vals = self._prepare_credit_account_vals(company, default_account_code, vals)
        else:
            default_account_vals = {}

        default_account = self.env['account.account'].create(default_account_vals)
        if default_account:
            self.env['ir.model.data']._update_xmlids([
                {
                    'xml_id': f"account.{company.id}_{journal_type}_journal_default_account_{default_account.id}",
                    'record': default_account,
                    'noupdate': True,
                }
            ])
        return default_account.id