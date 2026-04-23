def default_get(self, fields):
        self_ctx = self.with_context(is_statement_line=True)
        defaults = super(AccountBankStatementLine, self_ctx).default_get(fields)
        if 'journal_id' in fields and not defaults.get('journal_id'):
            defaults['journal_id'] = self_ctx.env['account.move']._search_default_journal().id

        if 'date' in fields and not defaults.get('date') and 'journal_id' in defaults:
            # copy the date and statement from the latest transaction of the same journal to help the user
            # to enter the next transaction, they do not have to enter the date and the statement every time until the
            # statement is completed. It is only possible if we know the journal that is used, so it can only be done
            # in a view in which the journal is already set and so is single journal view.
            last_line = self.search([
                ('journal_id', '=', defaults['journal_id']),
                ('state', '=', 'posted'),
            ], limit=1)
            statement = last_line.statement_id
            if statement:
                defaults.setdefault('date', statement.date)
            elif last_line:
                defaults.setdefault('date', last_line.date)
        return defaults