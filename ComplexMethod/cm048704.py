def _compute_running_balance(self):
        # It looks back to find the latest statement and uses its balance_start as an anchor point for calculation, so
        # that the running balance is always relative to the latest statement. In this way we do not need to calculate
        # the running balance for all statement lines every time.
        # If there are statements inside the computed range, their balance_start has priority over calculated balance.
        # we have to compute running balance for draft lines because they are visible and also
        # the user can split on that lines, but their balance should be the same as previous posted line
        # we do the same for the canceled lines, in order to keep using them as anchor points

        record_by_id = {x.id: x for x in self}
        company2children = {
            company: self.env['res.company'].search([('id', 'child_of', company.id)])
            for company in self.journal_id.company_id
        }
        for journal in self.journal_id:
            journal_lines_indexes = self.filtered(lambda line: line.journal_id == journal)\
                .sorted('internal_index')\
                .mapped('internal_index')
            min_index, max_index = journal_lines_indexes[0], journal_lines_indexes[-1]

            # Find the oldest index for each journal.
            self.env['account.bank.statement'].flush_model(['first_line_index', 'journal_id', 'balance_start'])
            self.env.cr.execute(
                """
                    SELECT first_line_index, COALESCE(balance_start, 0.0)
                    FROM account_bank_statement
                    WHERE
                        first_line_index < %s
                        AND journal_id = %s
                    ORDER BY first_line_index DESC
                    LIMIT 1
                """,
                [min_index or '', journal.id],
            )
            current_running_balance = 0.0
            extra_clause = SQL()
            row = self.env.cr.fetchone()
            if row:
                starting_index, current_running_balance = row
                extra_clause = SQL("AND st_line.internal_index >= %s", starting_index)

            self.flush_model(['amount', 'move_id', 'statement_id', 'journal_id', 'internal_index'])
            self.env['account.bank.statement'].flush_model(['first_line_index', 'balance_start'])
            self.env['account.move'].flush_model(['state'])
            self.env.cr.execute(SQL(
                """
                    SELECT
                        st_line.id,
                        st_line.amount,
                        st.first_line_index = st_line.internal_index AS is_anchor,
                        COALESCE(st.balance_start, 0.0),
                        move.state
                    FROM account_bank_statement_line st_line
                    JOIN account_move move ON move.id = st_line.move_id
                    LEFT JOIN account_bank_statement st ON st.id = st_line.statement_id
                    WHERE
                        st_line.internal_index <= %s
                        AND st_line.journal_id = %s
                        AND st_line.company_id = ANY(%s)
                        %s
                    ORDER BY st_line.internal_index
                """,
                max_index or '',
                journal.id,
                company2children[journal.company_id].ids,
                extra_clause,
            ))
            pending_items = self
            for st_line_id, amount, is_anchor, balance_start, state in self.env.cr.fetchall():
                if is_anchor:
                    current_running_balance = balance_start
                if state == 'posted':
                    current_running_balance += amount
                if record_by_id.get(st_line_id):
                    record_by_id[st_line_id].running_balance = current_running_balance
                    pending_items -= record_by_id[st_line_id]
            # Lines manually deleted from the form view still require to have a value set here, as the field is computed and non-stored.
            for item in pending_items:
                item.running_balance = item.running_balance