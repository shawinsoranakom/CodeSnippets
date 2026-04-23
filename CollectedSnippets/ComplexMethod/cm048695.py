def default_get(self, fields):
        # EXTENDS base
        defaults = super().default_get(fields)

        if 'line_ids' not in fields:
            return defaults

        active_ids = self.env.context.get('active_ids', [])
        context_split_line_id = self.env.context.get('split_line_id')
        context_st_line_id = self.env.context.get('st_line_id')
        lines = None
        # creating statements with split button
        if context_split_line_id:
            current_st_line = self.env['account.bank.statement.line'].browse(context_split_line_id)
            line_before = self.env['account.bank.statement.line'].search(
                domain=[
                    ('internal_index', '<', current_st_line.internal_index),
                    ('journal_id', '=', current_st_line.journal_id.id),
                    ('statement_id', '!=', current_st_line.statement_id.id),
                    ('statement_id', '!=', False),
                ],
                order='internal_index desc',
                limit=1,
            )
            lines = self.env['account.bank.statement.line'].search(
                domain=[
                    ('internal_index', '<=', current_st_line.internal_index),
                    ('internal_index', '>', line_before.internal_index or ''),
                    ('journal_id', '=', current_st_line.journal_id.id),
                ],
                order='internal_index desc',
            )
        # single line edit
        elif context_st_line_id and len(active_ids) <= 1:
            lines = self.env['account.bank.statement.line'].browse(context_st_line_id)
        # multi edit
        elif context_st_line_id and len(active_ids) > 1:
            lines = self.env['account.bank.statement.line'].browse(active_ids).sorted()
            if len(lines.journal_id) > 1:
                raise UserError(_("A statement should only contain lines from the same journal."))
            # Check that the selected lines are contiguous (there might be canceled lines between the indexes and these should be ignored from the check)
            indexes = lines.mapped('internal_index')
            lines_between = self.env['account.bank.statement.line'].search([
                ('internal_index', '>=', min(indexes)),
                ('internal_index', '<=', max(indexes)),
                ('journal_id', '=', lines.journal_id.id),
            ])
            canceled_lines = lines_between.filtered(lambda l: l.state == 'cancel')
            if len(lines) != len(lines_between - canceled_lines):
                raise UserError(_("Unable to create a statement due to missing transactions. You may want to reorder the transactions before proceeding."))
            lines |= canceled_lines

        if lines:
            defaults['line_ids'] = [Command.set(lines.ids)]

        return defaults