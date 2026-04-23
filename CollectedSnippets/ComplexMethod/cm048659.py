def copy_data(self, default=None):
        default = dict(default or {})
        vals_list = super().copy_data(default)
        default_date = fields.Date.to_date(default.get('date'))
        for move, vals in zip(self, vals_list):
            if move.move_type in ('out_invoice', 'in_invoice'):
                vals['line_ids'] = [
                    (command, _id, line_vals)
                    for command, _id, line_vals in vals['line_ids']
                    if command == Command.CREATE
                ]
            elif move.move_type == 'entry':
                if 'partner_id' not in vals or not self.env.context.get('move_reverse_cancel', False):
                    vals['partner_id'] = False
            user_fiscal_lock_date = move.company_id._get_user_fiscal_lock_date(move.journal_id)
            if (default_date or move.date) <= user_fiscal_lock_date:
                vals['date'] = user_fiscal_lock_date + timedelta(days=1)
            if not move.journal_id.active and 'journal_id' in vals:
                del vals['journal_id']
        return vals_list