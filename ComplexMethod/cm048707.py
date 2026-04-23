def create(self, vals_list):
        # OVERRIDE
        counterpart_account_ids = []

        for vals in vals_list:
            if 'statement_id' in vals and 'journal_id' not in vals:
                statement = self.env['account.bank.statement'].browse(vals['statement_id'])
                # Ensure the journal is the same as the statement one.
                # journal_id is a required field in the view, so it should be always available if the user
                # is creating the record, however, if a sync/import modules tries to add a line to an existing
                # statement they can omit the journal field because it can be obtained from the statement
                if statement.journal_id:
                    vals['journal_id'] = statement.journal_id.id

            # Avoid having the same foreign_currency_id as currency_id.
            if vals.get('journal_id') and vals.get('foreign_currency_id'):
                journal = self.env['account.journal'].browse(vals['journal_id'])
                journal_currency = journal.currency_id or journal.company_id.currency_id
                if vals['foreign_currency_id'] == journal_currency.id:
                    vals['foreign_currency_id'] = None
                    vals['amount_currency'] = 0.0

            # Force the move_type to avoid inconsistency with residual 'default_move_type' inside the context.
            vals['move_type'] = 'entry'

            # Hack to force different account instead of the suspense account.
            counterpart_account_ids.append(vals.pop('counterpart_account_id', None))

            #Set the amount to 0 if it's not specified.
            if 'amount' not in vals:
                vals['amount'] = 0

        st_lines = super(AccountBankStatementLine, self.with_context(is_statement_line=True)).create([{
            'name': False,
            **vals,
        } for vals in vals_list])
        to_create_lines_vals = []
        for i, (st_line, vals) in enumerate(zip(st_lines, vals_list)):
            if 'line_ids' not in vals_list[i]:
                to_create_lines_vals.extend(
                    line_vals
                    for line_vals in st_line._prepare_move_line_default_vals(counterpart_account_ids[i])
                )
            to_write = {'statement_line_id': st_line.id, 'narration': st_line.narration, 'name': False}
            with self.env.protecting(self.env['account.move']._get_protected_vals(vals, st_line)):
                st_line.move_id.with_context(clear_sequence_mixin_cache=False).write(to_write)
        self.env['account.move.line'].create(to_create_lines_vals)
        self.env.add_to_compute(self.env['account.move']._fields['name'], st_lines.move_id)

        # Otherwise field narration will be recomputed silently (at next flush) when writing on partner_id
        self.env.remove_to_compute(self.env['account.move']._fields['narration'], st_lines.move_id)

        # No need for the user to manage their status (from 'Draft' to 'Posted')
        st_lines.move_id.action_post()
        return st_lines.with_env(self.env)