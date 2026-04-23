def _synchronize_to_moves(self, changed_fields):
        """ Update the account.move regarding the modified account.bank.statement.line.
        :param changed_fields: A list containing all modified fields on account.bank.statement.line.
        """
        if self.env.context.get('skip_account_move_synchronization'):
            return

        if not any(field_name in changed_fields for field_name in (
            'payment_ref', 'amount', 'amount_currency',
            'foreign_currency_id', 'currency_id', 'partner_id',
        )):
            return

        for st_line in self.with_context(skip_account_move_synchronization=True):
            liquidity_lines, suspense_lines, other_lines = st_line._seek_for_lines()
            journal = st_line.journal_id
            # bypassing access rights restrictions for branch-specific users in a branch company environment.
            company_currency = journal.company_id.sudo().currency_id
            journal_currency = journal.currency_id if journal.currency_id != company_currency else False

            line_vals_list = st_line._prepare_move_line_default_vals()
            line_ids_commands = [(1, liquidity_lines.id, line_vals_list[0])]

            if suspense_lines:
                line_ids_commands.append((1, suspense_lines.id, line_vals_list[1]))
            else:
                line_ids_commands.append((0, 0, line_vals_list[1]))

            for line in other_lines:
                line_ids_commands.append((2, line.id))

            st_line_vals = {
                'currency_id': (st_line.foreign_currency_id or journal_currency or company_currency).id,
                'line_ids': line_ids_commands,
            }
            if st_line.move_id.journal_id != journal:
                st_line_vals['journal_id'] = journal.id
            if st_line.move_id.partner_id != st_line.partner_id:
                st_line_vals['partner_id'] = st_line.partner_id.id
            st_line.move_id.with_context(skip_readonly_check=True).write(st_line_vals)