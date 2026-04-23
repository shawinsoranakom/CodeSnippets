def _do_action_change_period(self, move_vals):
        accrual_account = self.revenue_accrual_account if self.account_type == 'income' else self.expense_accrual_account

        created_moves = self.env['account.move'].create(move_vals)
        created_moves._post()

        destination_move = created_moves[0]
        destination_move_offset = 0
        destination_messages = []
        accrual_move_messages = defaultdict(lambda: [])
        accrual_move_offsets = defaultdict(int)
        for move in self.move_line_ids.move_id:
            amount = sum((self.move_line_ids._origin & move.line_ids).mapped('balance'))
            accrual_move = created_moves[1:].filtered(lambda m: m.date == self._get_lock_safe_date(move.date))

            if accrual_account.reconcile and accrual_move.state == 'posted' and destination_move.state == 'posted':
                destination_move_lines = destination_move.mapped('line_ids').filtered(lambda line: line.account_id == accrual_account)[destination_move_offset:destination_move_offset+2]
                destination_move_offset += 2
                accrual_move_lines = accrual_move.mapped('line_ids').filtered(lambda line: line.account_id == accrual_account)[accrual_move_offsets[accrual_move]:accrual_move_offsets[accrual_move]+2]
                accrual_move_offsets[accrual_move] += 2
                (accrual_move_lines + destination_move_lines).filtered(lambda line: not line.currency_id.is_zero(line.balance)).reconcile()
            body = Markup("%(title)s<ul><li>%(link1)s %(second)s</li><li>%(link2)s %(third)s</li></ul>") % {
                'title': _("Adjusting Entries have been created for this invoice:"),
                'link1': self._format_move_link(accrual_move),
                'second': self._format_strings(_("cancelling {percent}%% of {amount}"), move, amount),
                'link2': self._format_move_link(destination_move),
                'third': self._format_strings(_("postponing it to {new_date}"), move, amount),
            }
            move.message_post(body=body)
            destination_messages += [
                self._format_strings(
                    escape(_("Adjusting Entry {link} {percent}%% of {amount} recognized from {date}")),
                    move, amount,
                )
            ]
            accrual_move_messages[accrual_move] += [
                self._format_strings(
                    escape(_("Adjusting Entry {link} {percent}%% of {amount} recognized on {new_date}")),
                    move, amount,
                )
            ]

        destination_move.message_post(body=Markup('<br/>\n').join(destination_messages))
        for accrual_move, messages in accrual_move_messages.items():
            accrual_move.message_post(body=Markup('<br/>\n').join(messages))

        # open the generated entries
        action = {
            'name': _('Generated Entries'),
            'domain': [('id', 'in', created_moves.ids)],
            'res_model': 'account.move',
            'view_mode': 'list,form',
            'type': 'ir.actions.act_window',
            'views': [(self.env.ref('account.view_move_tree').id, 'list'), (False, 'form')],
        }
        if len(created_moves) == 1:
            action.update({'view_mode': 'form', 'res_id': created_moves.id})
        return action