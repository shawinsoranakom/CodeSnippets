def _prepare_qty_delivered(self):
        delivered_qties = super()._prepare_qty_delivered()
        for order_line in self:
            if order_line.qty_delivered_method == 'stock_move':
                boms = order_line.move_ids.filtered(lambda m: m.state != 'cancel').bom_line_id.bom_id
                # We fetch the BoMs of type kits linked to the order_line,
                # the we keep only the one related to the finished produst.
                # This bom should be the only one since bom_line_id was written on the moves
                relevant_bom = boms.filtered(lambda b: b.type == 'phantom' and
                        (b.product_id == order_line.product_id or
                        (b.product_tmpl_id == order_line.product_id.product_tmpl_id and not b.product_id)))
                if not relevant_bom:
                    relevant_bom = boms._bom_find(order_line.product_id, company_id=order_line.company_id.id, bom_type='phantom')[order_line.product_id]
                if relevant_bom:
                    moves = order_line.move_ids.filtered(lambda m: m.state == 'done' and m.location_dest_usage != 'inventory')
                    filters = {
                        # in/out perspective w/ respect to moves is flipped for sale order document
                        'incoming_moves': lambda m:
                            m._is_outgoing() and
                            (not m.origin_returned_move_id or (m.origin_returned_move_id and m.to_refund)),
                        'outgoing_moves': lambda m:
                            m._is_incoming() and m.to_refund,
                    }
                    order_qty = order_line.product_uom_id._compute_quantity(order_line.product_uom_qty, relevant_bom.product_uom_id)
                    qty_delivered = moves._compute_kit_quantities(order_line.product_id, order_qty, relevant_bom, filters)
                    delivered_qties[order_line] += relevant_bom.product_uom_id._compute_quantity(qty_delivered, order_line.product_uom_id)

                # If no relevant BOM is found, fall back on the all-or-nothing policy. This happens
                # when the product sold is made only of kits. In this case, the BOM of the stock moves
                # do not correspond to the product sold => no relevant BOM.
                elif boms:
                    # if the move is ingoing, the product **sold** has delivered qty 0
                    if all(m.state == 'done' and m.location_dest_id.usage == 'customer' for m in order_line.move_ids):
                        delivered_qties[order_line] = order_line.product_uom_qty
                    else:
                        delivered_qties[order_line] = 0.0
        return delivered_qties