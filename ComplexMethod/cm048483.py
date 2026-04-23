def _recompute_state(self):
        if self.env.context.get('preserve_state'):
            return
        moves_state_to_write = defaultdict(set)
        for move in self:
            rounding = move.product_uom.rounding
            if move.state in ('cancel', 'done') or (move.state == 'draft' and not move.quantity):
                continue
            elif float_compare(move.quantity, move.product_uom_qty, precision_rounding=rounding) >= 0:
                moves_state_to_write['assigned'].add(move.id)
            elif move.quantity and float_compare(move.quantity, move.product_uom_qty, precision_rounding=rounding) <= 0:
                moves_state_to_write['partially_available'].add(move.id)
            elif (move.procure_method == 'make_to_order' and not move.move_orig_ids) or\
                 (move.move_orig_ids and any(orig.product_uom.compare(orig.product_uom_qty, 0) > 0
                                             and orig.state not in ('done', 'cancel') for orig in move.move_orig_ids)):
                # In the process of merging a negative move, we may still have a negative move in the move_orig_ids at that point.
                moves_state_to_write['waiting'].add(move.id)
            else:
                moves_state_to_write['confirmed'].add(move.id)
        for state, moves_ids in moves_state_to_write.items():
            self.browse(moves_ids).filtered(lambda m: m.state != state).state = state