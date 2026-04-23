def _compute_show_check_availability(self):
        """ According to `picking.show_check_availability`, the "check availability" button will be
        displayed in the form view of a picking.
        """
        for picking in self:
            if picking.state not in ('confirmed', 'waiting', 'assigned'):
                picking.show_check_availability = False
                continue
            if all(m.picked or m.product_uom_qty == m.quantity for m in picking.move_ids):
                picking.show_check_availability = False
                continue
            picking.show_check_availability = any(
                move.state in ('waiting', 'confirmed', 'partially_available') and
                move.product_uom.compare(move.product_uom_qty, 0)
                for move in picking.move_ids
            )