def _get_relevant_state_among_moves(self):
        res = super()._get_relevant_state_among_moves()
        if res == 'partially_available'\
                and self.raw_material_production_id\
                and all(move.should_consume_qty and move.product_uom.compare(move.quantity, move.should_consume_qty) >= 0
                        or (move.product_uom.compare(move.quantity, move.product_uom_qty) >= 0 or (move.manual_consumption and move.picked))
                        for move in self):
            res = 'assigned'
        return res