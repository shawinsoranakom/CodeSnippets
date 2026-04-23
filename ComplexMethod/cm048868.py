def _action_synch_order(self):
        purchase_order_lines_vals = []
        for move in self:
            purchase_order = move.picking_id.purchase_id or move.picking_id.return_id.purchase_id
            # Creates new PO line only when pickings linked to a purchase order and
            # for moves with qty. done and not already linked to a PO line.
            if not purchase_order \
                or (move.location_id.usage not in ['supplier', 'transit'] and not (move.location_dest_id.usage == 'supplier' and move.to_refund)) \
                or move.purchase_line_id \
                or not move.picked:
                continue
            product = move.product_id
            if line := purchase_order.order_line.filtered(lambda l: l.product_id == product):
                move.purchase_line_id = line[:1]
                continue
            quantity = move.quantity
            if move.location_dest_id.usage in ['supplier', 'transit']:
                quantity *= -1
            po_line_vals = {
                'move_ids': [Command.link(move.id)],
                'order_id': purchase_order.id,
                'product_id': product.id,
                'product_qty': 0,
                'product_uom_id': move.product_uom.id,
                'qty_received': quantity
            }
            if product.purchase_method == 'purchase':
                # No unit price if the product is purchased on the ordered qty.
                po_line_vals['price_unit'] = 0
            purchase_order_lines_vals.append(po_line_vals)
        if purchase_order_lines_vals:
            self.env['purchase.order.line'].with_context(bypass_move_update=True).create(purchase_order_lines_vals)
        return super()._action_synch_order()