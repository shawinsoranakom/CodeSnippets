def _sync_unbalanced_lines(self, container):
        def has_tax(move):
            return bool(move.line_ids.tax_ids)

        move_had_tax = {move: has_tax(move) for move in container['records']}
        yield
        # Skip posted moves.
        for move in (x for x in container['records'] if x.state != 'posted'):
            if not has_tax(move) and not move_had_tax.get(move):
                continue  # only manage automatically unbalanced when taxes are involved
            if move_had_tax.get(move) and not has_tax(move):
                # taxes have been removed, the tax sync is deactivated so we need to clear everything here
                move.line_ids.filtered('tax_line_id').unlink()
                move.line_ids.tax_tag_ids = [Command.set([])]

            # Set the balancing line's balance and amount_currency to zero,
            # so that it does not interfere with _get_unbalanced_moves() below.
            balance_name = _('Automatic Balancing Line')
            existing_balancing_line = move.line_ids.filtered(lambda line: line.name == balance_name)
            if existing_balancing_line:
                existing_balancing_line.balance = existing_balancing_line.amount_currency = 0.0

            # Create an automatic balancing line to make sure the entry can be saved/posted.
            # If such a line already exists, we simply update its amounts.
            unbalanced_moves = self._get_unbalanced_moves({'records': move})
            if isinstance(unbalanced_moves, list) and len(unbalanced_moves) == 1:
                dummy, debit, credit = unbalanced_moves[0]

                vals = {'balance': credit - debit}
                if existing_balancing_line:
                    existing_balancing_line.write(vals)
                else:
                    vals.update({
                        'name': balance_name,
                        'move_id': move.id,
                        'account_id': move._get_automatic_balancing_account(),
                        'currency_id': move.currency_id.id,
                        # A balancing line should never have default taxes applied to it, it doesn't work well and wouldn't make much sense.
                        'tax_ids': False,
                    })
                    self.env['account.move.line'].create(vals)