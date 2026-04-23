def _create_repair_order(self):
        new_repair_vals = []
        for line in self:
            # One RO for each line with at least a quantity of 1, quantities > 1 don't create multiple ROs
            if any(line.id == ro.sale_order_line_id.id for ro in line.order_id.sudo().repair_order_ids) and line.product_uom_id.compare(line.product_uom_qty, 0) > 0:
                binded_ro_ids = line.order_id.sudo().repair_order_ids.filtered(lambda ro: ro.sale_order_line_id.id == line.id and ro.state == 'cancel')
                binded_ro_ids.action_repair_cancel_draft()
                binded_ro_ids._action_repair_confirm()
                continue
            if line.product_template_id.sudo().service_tracking != 'repair' or line.move_ids.sudo().repair_id or line.product_uom_id.compare(line.product_uom_qty, 0) <= 0:
                continue

            order = line.order_id
            new_repair_vals.append({
                'state': 'confirmed',
                'partner_id': order.partner_id.id,
                'sale_order_id': order.id,
                'sale_order_line_id': line.id,
                'picking_type_id': order.warehouse_id.repair_type_id.id,
            })

        if new_repair_vals:
            self.env['repair.order'].sudo().create(new_repair_vals)