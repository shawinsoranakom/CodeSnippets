def _update_stock_move_value(self, old_qty_by_ml=None):
        move_to_update_ids = set()
        if not old_qty_by_ml:
            old_qty_by_ml = {}

        for move, mls in self.grouped('move_id').items():
            if not (move.is_in or move.is_out):
                continue
            if move.is_in:
                move_to_update_ids.add(move.id)
            elif move.is_out:
                delta = sum(
                    ml.quantity - old_qty_by_ml.get(ml, 0)
                    for ml in mls
                    if not ml._should_exclude_for_valuation()
                )
                if delta:
                    move._set_value(correction_quantity=delta)
        if moves_to_update := self.env['stock.move'].browse(move_to_update_ids):
            moves_to_update._set_value()