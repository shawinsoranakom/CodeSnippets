def sync_from_ui(self, orders):
        data = super().sync_from_ui(orders)
        if len(orders) == 0:
            return data

        AccountTax = self.env['account.tax']
        pos_orders = self.browse([o['id'] for o in data["pos.order"]])
        for pos_order in pos_orders:
            # TODO: the way to retrieve the sale order in not consistent... is it a bad code or intended?
            used_pos_lines = pos_order.lines.sale_order_origin_id.order_line.pos_order_line_ids
            downpayment_pos_order_lines = pos_order.lines.filtered(lambda line: (
                line not in used_pos_lines
                and line.product_id == pos_order.config_id.down_payment_product_id
            ))
            so_x_pos_order_lines = downpayment_pos_order_lines\
                .grouped(lambda l: l.sale_order_origin_id or l.refunded_orderline_id.sale_order_origin_id)
            sale_orders = self.env['sale.order']
            for sale_order, pos_order_lines in so_x_pos_order_lines.items():
                if not sale_order:
                    continue

                sale_orders += sale_order
                down_payment_base_lines = pos_order_lines._prepare_tax_base_line_values()
                AccountTax._add_tax_details_in_base_lines(down_payment_base_lines, sale_order.company_id)
                AccountTax._round_base_lines_tax_details(down_payment_base_lines, sale_order.company_id)

                sale_order_sudo = sale_order.sudo()
                sale_order_sudo._create_down_payment_section_line_if_needed()
                sale_order_sudo._create_down_payment_lines_from_base_lines(down_payment_base_lines)

            # Confirm the unconfirmed sale orders that are linked to the sale order lines.
            so_lines = pos_order.lines.mapped('sale_order_line_id')
            sale_orders |= so_lines.mapped('order_id')
            if pos_order.state != 'draft':
                for sale_order in sale_orders.filtered(lambda so: so.state in ['draft', 'sent']):
                    sale_order.action_confirm()

            # update the demand qty in the stock moves related to the sale order line
            # flush the qty_delivered to make sure the updated qty_delivered is used when
            # updating the demand value
            so_lines.flush_recordset(['qty_delivered'])
            # track the waiting pickings
            waiting_picking_ids = set()
            for so_line in so_lines:
                so_line_stock_move_ids = so_line.move_ids.reference_ids.move_ids
                for stock_move in so_line.move_ids:
                    picking = stock_move.picking_id
                    if not picking.state in ['waiting', 'confirmed', 'assigned']:
                        continue

                    def get_expected_qty_to_ship_later():
                        pos_pickings = so_line.pos_order_line_ids.order_id.picking_ids
                        if pos_pickings and all(pos_picking.state in ['confirmed', 'assigned'] for pos_picking in pos_pickings):
                            return sum((so_line._convert_qty(so_line, pos_line.qty, 'p2s') for pos_line in
                                        so_line.pos_order_line_ids if so_line.product_id.type != 'service'), 0)
                        return 0

                    qty_delivered = max(so_line.qty_delivered, get_expected_qty_to_ship_later())
                    new_qty = so_line.product_uom_qty - qty_delivered
                    if stock_move.product_uom.compare(new_qty, 0) <= 0:
                        new_qty = 0
                    stock_move.product_uom_qty = so_line.compute_uom_qty(new_qty, stock_move, False)
                    # If the product is delivered with more than one step, we need to update the quantity of the other steps
                    for move in so_line_stock_move_ids.filtered(lambda m: m.state in ['waiting', 'confirmed', 'assigned'] and m.product_id == stock_move.product_id):
                        move.product_uom_qty = stock_move.product_uom_qty
                        waiting_picking_ids.add(move.picking_id.id)
                    waiting_picking_ids.add(picking.id)

            def is_product_uom_qty_zero(move):
                return move.product_uom.is_zero(move.product_uom_qty)

            # cancel the waiting pickings if each product_uom_qty of move is zero
            for picking in self.env['stock.picking'].browse(waiting_picking_ids):
                if all(is_product_uom_qty_zero(move) for move in picking.move_ids):
                    picking.action_cancel()
                else:
                    # We make sure that the original picking still has the correct quantity reserved
                    picking.action_assign()

        return data