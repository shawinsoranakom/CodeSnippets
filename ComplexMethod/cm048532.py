def _do_action_change_account(self, move_vals):
        new_move = self.env['account.move'].create(move_vals)
        new_move._post()

        # Group lines
        grouped_lines = defaultdict(lambda: self.env['account.move.line'])
        destination_lines = self.move_line_ids.filtered(lambda x: x.account_id == self.destination_account_id)
        for line in self.move_line_ids - destination_lines:
            grouped_lines[(line.partner_id, line.currency_id, line.account_id)] += line

        # Reconcile
        for (partner, currency, account), lines in grouped_lines.items():
            if account.reconcile:
                to_reconcile = lines + new_move.line_ids.filtered(lambda x: x.account_id == account and x.partner_id == partner and x.currency_id == currency)
                to_reconcile.reconcile()

            if destination_lines and self.destination_account_id.reconcile:
                to_reconcile = destination_lines + new_move.line_ids.filtered(lambda x: x.account_id == self.destination_account_id and x.partner_id == partner and x.currency_id == currency)
                to_reconcile.reconcile()

        # Log the operation on source moves
        acc_transfer_per_move = defaultdict(lambda: defaultdict(lambda: 0))  # dict(move, dict(account, balance))
        for line in self.move_line_ids:
            acc_transfer_per_move[line.move_id][line.account_id] += line.balance

        for move, balances_per_account in acc_transfer_per_move.items():
            message_to_log = self._format_transfer_source_log(balances_per_account, new_move)
            if message_to_log:
                move.message_post(body=message_to_log)

        # Log on target move as well
        new_move.message_post(body=self._format_new_transfer_move_log(acc_transfer_per_move))

        return {
            'name': _("Transfer"),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'account.move',
            'res_id': new_move.id,
        }