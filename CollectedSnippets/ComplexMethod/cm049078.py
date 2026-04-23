def write(self, vals):
        analytic_move_to_recompute = set()
        if 'quantity' in vals or 'move_id' in vals:
            for move_line in self:
                move_id = vals.get('move_id', move_line.move_id.id)
                analytic_move_to_recompute.add(move_id)
        valuation_fields = ['quantity', 'location_id', 'location_dest_id', 'owner_id', 'quant_id', 'lot_id']
        valuation_trigger = any(field in vals for field in valuation_fields)
        qty_by_ml = {}
        if valuation_trigger:
            qty_by_ml = {ml: ml.quantity for ml in self if ml.move_id.is_in or ml.move_id.is_out}
        res = super().write(vals)
        if valuation_trigger and qty_by_ml:
            self._update_stock_move_value(qty_by_ml)
        if analytic_move_to_recompute:
            self.env['stock.move'].browse(analytic_move_to_recompute).sudo()._create_analytic_move()
        return res