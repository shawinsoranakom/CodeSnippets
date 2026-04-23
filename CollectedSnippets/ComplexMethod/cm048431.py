def unlink(self):
        precision = self.env['decimal.precision'].precision_get('Product Unit')
        for ml in self:
            # Unlinking a move line should unreserve.
            if not float_is_zero(ml.quantity_product_uom, precision_digits=precision) and ml.move_id and not ml.move_id._should_bypass_reservation(ml.location_id):
                self.env['stock.quant']._update_reserved_quantity(ml.product_id, ml.location_id, -ml.quantity_product_uom, lot_id=ml.lot_id, package_id=ml.package_id, owner_id=ml.owner_id, strict=True)
        moves = self.mapped('move_id')
        packages = self.env['stock.package'].browse(self.result_package_id._get_all_package_dest_ids())
        res = super().unlink()
        if moves:
            # Add with_prefetch() to set the _prefecht_ids = _ids
            # because _prefecht_ids generator look lazily on the cache of move_id
            # which is clear by the unlink of move line
            moves.with_prefetch()._recompute_state()
        if packages:
            # Clear the dest from packages if not linked to any active picking
            packages.filtered(lambda p: p.package_dest_id and not p.picking_ids).package_dest_id = False
        return res