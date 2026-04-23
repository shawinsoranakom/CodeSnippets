def _check_backorder(self):
        prec = self.env["decimal.precision"].precision_get("Product Unit")
        backorder_pickings = self.browse()
        for picking in self:
            if picking.picking_type_id.create_backorder != 'ask':
                continue
            if any(
                    (move.product_uom_qty and not move.picked) or
                    float_compare(move._get_picked_quantity(), move.product_uom_qty, precision_digits=prec) < 0
                    for move in picking.move_ids
                    if move.state != 'cancel'
            ):
                backorder_pickings |= picking
        return backorder_pickings