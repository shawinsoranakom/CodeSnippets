def default_get(self, fields):
        res = super().default_get(fields)
        if not set(fields) & set(['move_line_ids', 'company_id']):
            return res

        if self.env.context.get('active_model') != 'account.move.line' or not self.env.context.get('active_ids'):
            raise UserError(_('This can only be used on journal items'))
        move_line_ids = self.env['account.move.line'].browse(self.env.context['active_ids'])
        res['move_line_ids'] = [(6, 0, move_line_ids.ids)]

        if any(move.state != 'posted' for move in move_line_ids.mapped('move_id')):
            raise UserError(_("Oops! You can only change the period or account for posted entries! Other ones aren't up for an adventure like that!"))
        if any(move_line.reconciled for move_line in move_line_ids):
            raise UserError(_("Oops! You can only change the period or account for items that are not yet reconciled! Other ones aren't up for an adventure like that!"))
        if any(line.company_id.root_id != move_line_ids[0].company_id.root_id for line in move_line_ids):
            raise UserError(_('You cannot use this wizard on journal entries belonging to different companies.'))
        res['company_id'] = move_line_ids[0].company_id.root_id.id

        allowed_actions = set(dict(self._fields['action'].selection))
        if self.env.context.get('default_action'):
            allowed_actions = {self.env.context['default_action']}
        if any(line.account_id.account_type != move_line_ids[0].account_id.account_type for line in move_line_ids):
            allowed_actions.discard('change_period')
        if not allowed_actions:
            raise UserError(_('No possible action found with the selected lines.'))
        res['action'] = allowed_actions.pop()
        return res