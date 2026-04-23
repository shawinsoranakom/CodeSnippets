def _compute_from_moves(self):
        for record in self:
            move_ids = record.move_ids._origin
            record.residual = len(move_ids) == 1 and move_ids.amount_residual or 0
            record.currency_id = len(move_ids.currency_id) == 1 and move_ids.currency_id or False
            record.move_type = move_ids.move_type if len(move_ids) == 1 else (any(move.move_type in ('in_invoice', 'out_invoice') for move in move_ids) and 'some_invoice' or False)