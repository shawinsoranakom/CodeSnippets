def button_cancel(self):
        order_lines_ids = OrderedSet()
        pickings_to_cancel_ids = OrderedSet()

        for order in self:
            # If the product is MTO, change the procure_method of the closest move to purchase to MTS.
            # The purpose is to link the po that the user will manually generate to the existing moves's chain.
            if order.state in ('draft', 'sent', 'to approve', 'purchase'):
                order_lines_ids.update(order.order_line.ids)
            pickings_to_cancel_ids.update(order.picking_ids.filtered(lambda r: r.state not in ('cancel', 'done')).ids)
            # We can't cancel pickings that are already done, so we leave them untouched but log a note about it.
            for picking in order.picking_ids:
                if picking.state == 'done':
                    picking.message_post(body=self.env._("The purchase order %s this receipt is linked to was cancelled.", order._get_html_link()))

        order_lines = self.env['purchase.order.line'].browse(order_lines_ids)
        moves_to_cancel_ids = OrderedSet()
        moves_to_recompute_ids = OrderedSet()
        for order_line in order_lines:
            moves_to_cancel_ids.update(order_line.move_ids.filtered(lambda move: move.state != 'done').ids)
            if order_line.move_dest_ids:
                move_dest_ids = order_line.move_dest_ids.filtered(lambda move: move.state != 'done' and move.location_dest_usage != 'inventory')
                moves_to_mts = move_dest_ids.filtered(lambda move: move.rule_id.route_id != move.location_dest_id.warehouse_id.reception_route_id)
                move_dest_ids -= moves_to_mts
                moves_to_recompute_ids.update(moves_to_mts.ids)
                moves_to_unlink = move_dest_ids.filtered(lambda m: len(m.created_purchase_line_ids.ids) > 1)
                if moves_to_unlink:
                    moves_to_unlink.created_purchase_line_ids = [Command.unlink(order_line.id)]
                move_dest_ids -= moves_to_unlink
                if order_line.propagate_cancel:
                    moves_to_cancel_ids.update(move_dest_ids.ids)
                else:
                    moves_to_recompute_ids.update(move_dest_ids.ids)

        if moves_to_cancel_ids:
            moves_to_cancel = self.env['stock.move'].browse(moves_to_cancel_ids)
            moves_to_cancel._action_cancel()

        if moves_to_recompute_ids:
            moves_to_recompute = self.env['stock.move'].browse(moves_to_recompute_ids)
            moves_to_recompute.write({'procure_method': 'make_to_stock'})
            moves_to_recompute._recompute_state()

        if pickings_to_cancel_ids:
            pikings_to_cancel = self.env['stock.picking'].browse(pickings_to_cancel_ids)
            pikings_to_cancel.action_cancel()

        return super().button_cancel()