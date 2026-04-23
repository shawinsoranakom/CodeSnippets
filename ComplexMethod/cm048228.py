def action_repair_done(self):
        """ Creates stock move for final product of repair order.
        Writes move_id and move_ids state to 'done'.
        Writes repair order state to 'Repaired'.
        @return: True
        """

        precision = self.env['decimal.precision'].precision_get('Product Unit')
        product_move_vals = []

        # Cancel moves with 0 quantity
        self.move_ids.filtered(lambda m: m.product_uom.is_zero(m.quantity))._action_cancel()

        no_service_policy = 'service_policy' not in self.env['product.template']
        #SOL qty delivered = repair.move_ids.quantity
        for repair in self:
            if all(not move.picked for move in repair.move_ids):
                repair.move_ids.picked = True
            if repair.sale_order_line_id:
                ro_origin_product = repair.sale_order_line_id.product_template_id
                # TODO: As 'service_policy' only appears with 'sale_project' module, isolate conditions related to this field in a 'sale_project_repair' module if it's worth
                if ro_origin_product.type == 'service' and (no_service_policy or ro_origin_product.service_policy == 'ordered_prepaid'):
                    repair.sale_order_line_id.qty_delivered = repair.sale_order_line_id.product_uom_qty
            if not repair.product_id:
                continue

            if repair.product_id.product_tmpl_id.tracking != 'none' and not repair.lot_id:
                raise ValidationError(_(
                    "Serial number is required for product to repair : %s",
                    repair.product_id.display_name
                ))

            # Try to create move with the appropriate owner
            owner_id = False
            available_qty_owner = self.env['stock.quant']._get_available_quantity(repair.product_id, repair.location_id, repair.lot_id, owner_id=repair.partner_id, strict=True)
            if float_compare(available_qty_owner, repair.product_qty, precision_digits=precision) >= 0:
                owner_id = repair.partner_id.id

            product_move_vals.append({
                'product_id': repair.product_id.id,
                'product_uom': repair.product_uom.id or repair.product_id.uom_id.id,
                'product_uom_qty': repair.product_qty,
                'partner_id': repair.partner_id.id,
                'location_id': repair.product_location_src_id.id,
                'location_dest_id': repair.product_location_dest_id.id,
                'picked': True,
                'picking_id': False,
                'move_line_ids': [(0, 0, {
                    'product_id': repair.product_id.id,
                    'lot_id': repair.lot_id.id,
                    'product_uom_id': repair.product_uom.id or repair.product_id.uom_id.id,
                    'quantity': repair.product_qty,
                    'package_id': False,
                    'result_package_id': False,
                    'owner_id': owner_id,
                    'location_id': repair.product_location_src_id.id,
                    'company_id': repair.company_id.id,
                    'location_dest_id': repair.product_location_dest_id.id,
                    'consume_line_ids': [(6, 0, repair.move_ids.move_line_ids.ids)]
                })],
                'repair_id': repair.id,
                'origin': repair.name,
                'company_id': repair.company_id.id,
            })

        product_moves = self.env['stock.move'].create(product_move_vals)
        repair_move = {m.repair_id.id: m for m in product_moves}
        for repair in self:
            move_id = repair_move.get(repair.id, False)
            if move_id:
                repair.move_id = move_id
        all_moves = self.move_ids + product_moves
        all_moves._action_done(cancel_backorder=True)

        self.state = 'done'
        return True