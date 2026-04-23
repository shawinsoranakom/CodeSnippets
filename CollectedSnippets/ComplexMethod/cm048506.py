def default_get(self, fields):
        res = super(AccountMoveReversal, self).default_get(fields)
        move_ids = self.env['account.move'].browse(self.env.context['active_ids']) if self.env.context.get('active_model') == 'account.move' else self.env['account.move']

        if len(move_ids.company_id) > 1:
            raise UserError(_("All selected moves for reversal must belong to the same company."))

        if any(move.state != "posted" for move in move_ids):
            raise UserError(_(
                'To reverse a journal entry, it has to be posted first.'
            ))
        if 'company_id' in fields:
            res['company_id'] = move_ids.company_id.id or self.env.company.id
        if 'move_ids' in fields:
            res['move_ids'] = [(6, 0, move_ids.ids)]
        return res