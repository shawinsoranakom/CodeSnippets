def _action_done(self):
        res = super()._action_done()
        sale_order_lines_vals = []
        for move in self.move_ids:
            ref_sale = move.picking_id.reference_ids.sale_ids
            sale_order = ref_sale and ref_sale[0] or move.sale_line_id.order_id
            # Creates new SO line only when pickings linked to a sale order and
            # for moves with qty. done and not already linked to a SO line.
            if not sale_order or move.sale_line_id or not move.picked or not (
                (move.location_dest_id.usage in ['customer', 'transit'] and not move.move_dest_ids)
                or (move.location_id.usage == 'customer' and move.to_refund)
            ):
                continue
            product = move.product_id
            quantity = move.quantity
            if move.location_id.usage in ['customer', 'transit']:
                quantity *= -1

            so_line_vals = {
                'move_ids': [(4, move.id, 0)],
                'name': product.display_name,
                'order_id': sale_order.id,
                'product_id': product.id,
                'product_uom_qty': 0,
                'qty_delivered': quantity,
                'product_uom_id': move.product_uom.id,
            }
            so_line = sale_order.order_line.filtered(lambda sol: sol.product_id == product)
            if product.invoice_policy == 'delivery':
                # Check if there is already a SO line for this product to get
                # back its unit price (in case it was manually updated).
                if so_line:
                    so_line_vals['price_unit'] = so_line[0].price_unit
            elif product.invoice_policy == 'order':
                # No unit price if the product is invoiced on the ordered qty.
                so_line_vals['price_unit'] = 0
            # New lines should be added at the bottom of the SO (higher sequence number)
            if not so_line:
                so_line_vals['sequence'] = (
                    max(sale_order.order_line.mapped('sequence'), default=0) + len(sale_order_lines_vals) + 1
                )
            sale_order_lines_vals.append(so_line_vals)

        if sale_order_lines_vals:
            self.env['sale.order.line'].with_context(skip_procurement=True).create(sale_order_lines_vals)
        return res