def _search_default_journal(self):
        if self.statement_line_ids.statement_id.journal_id:
            return self.statement_line_ids.statement_id.journal_id[:1]

        journal_types = self._get_valid_journal_types()
        company = self.company_id or self.env.company
        domain = [
            *self.env['account.journal']._check_company_domain(company),
            ('type', 'in', journal_types),
        ]

        journal = None
        # the currency is not a hard dependence, it triggers via manual add_to_compute
        # avoid computing the currency before all it's dependences are set (like the journal...)
        if self.env.cache.contains(self, self._fields['currency_id']):
            currency_id = self.currency_id.id or self.env.context.get('default_currency_id')
            if currency_id and currency_id != company.currency_id.id:
                currency_domain = domain + [('currency_id', '=', currency_id)]
                journal = self.env['account.journal'].search(currency_domain, limit=1)

        if not journal:
            journal = self.env['account.journal'].search(domain, limit=1)

        if not journal:
            error_msg = self.env['account.journal']._build_no_journal_error_msg(company.display_name, journal_types)
            raise UserError(error_msg)

        return journal