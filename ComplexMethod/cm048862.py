def _create_or_update_picking(self):
        for line in self:
            if line.product_id and line.product_id.type == 'consu':
                rounding = line.product_uom_id.rounding
                if float_compare(line.product_qty, line.qty_invoiced, precision_rounding=rounding) < 0 and line.invoice_lines:
                    # If the quantity is now below the invoiced quantity, create an activity on the vendor bill
                    # inviting the user to create a refund.
                    line.invoice_lines[0].move_id.activity_schedule(
                        'mail.mail_activity_data_warning',
                        note=_('The quantities on your purchase order indicate less than billed. You should ask for a refund.'),
                        user_id=self.env.uid,
                    )

                # If the user increased quantity of existing line or created a new line
                # Give priority to the pickings related to the line
                moves_to_assign = line.order_id.picking_ids.move_ids.filtered(lambda m: not m.purchase_line_id and line.product_id == m.product_id)
                moves_to_assign.purchase_line_id = line.id
                line_pickings = line.move_ids.picking_id.filtered(lambda p: p.state not in ('done', 'cancel') and p.location_dest_id.usage in ('internal', 'transit', 'customer'))
                if line_pickings:
                    picking = line_pickings[0]
                else:
                    pickings = line.order_id.picking_ids.filtered(lambda x: x.state not in ('done', 'cancel') and x.location_dest_id.usage in ('internal', 'transit', 'customer'))
                    picking = pickings and pickings[0] or False
                if not picking:
                    if not line.product_qty > line.qty_received:
                        continue
                    res = line.order_id._prepare_picking()
                    picking = self.env['stock.picking'].create(res)

                moves = line._create_stock_moves(picking)
                moves._action_confirm()._action_assign()