def _update_reserved_quantity_vals(self, need, location_id, lot_id=None, package_id=None, owner_id=None, strict=True):
        self.ensure_one()
        if not lot_id:
            lot_id = self.env['stock.lot']
        if not package_id:
            package_id = self.env['stock.package']
        if not owner_id:
            owner_id = self.env['res.partner']

        quants = self.env['stock.quant'].with_context(packaging_uom_id=self.packaging_uom_id)._get_reserve_quantity(
            self.product_id, location_id, need, uom_id=self.product_uom,
            lot_id=lot_id, package_id=package_id, owner_id=owner_id, strict=strict)

        taken_quantity = 0
        rounding = self.env['decimal.precision'].precision_get('Product Unit')
        # Find a candidate move line to update or create a new one.
        candidate_lines = {}
        for line in self.move_line_ids:
            if line.result_package_id or line.product_id.tracking == 'serial':
                continue
            candidate_lines[line.location_id, line.lot_id, line.package_id, line.owner_id] = line
        move_line_vals = []
        grouped_quants = {}
        # Handle quants duplication
        for quant, quantity in quants:
            if (quant.location_id, quant.lot_id, quant.package_id, quant.owner_id) not in grouped_quants:
                grouped_quants[quant.location_id, quant.lot_id, quant.package_id, quant.owner_id] = [quant, quantity]
            else:
                grouped_quants[quant.location_id, quant.lot_id, quant.package_id, quant.owner_id][1] += quantity
        for reserved_quant, quantity in grouped_quants.values():
            taken_quantity += quantity
            to_update = candidate_lines.get((reserved_quant.location_id, reserved_quant.lot_id, reserved_quant.package_id, reserved_quant.owner_id))
            if to_update:
                uom_quantity = self.product_id.uom_id._compute_quantity(quantity, to_update.product_uom_id, rounding_method='HALF-UP')
                uom_quantity = float_round(uom_quantity, precision_digits=rounding)
                uom_quantity_back_to_product_uom = to_update.product_uom_id._compute_quantity(uom_quantity, self.product_id.uom_id, rounding_method='HALF-UP')
            if to_update and float_compare(quantity, uom_quantity_back_to_product_uom, precision_digits=rounding) == 0:
                to_update.with_context(reserved_quant=reserved_quant).quantity += uom_quantity
            else:
                if self.product_id.tracking == 'serial' and (self.picking_type_id.use_create_lots or self.picking_type_id.use_existing_lots):
                    vals_list = self._add_serial_move_line_to_vals_list(reserved_quant, quantity)
                    if vals_list:
                        move_line_vals += vals_list
                else:
                    move_line_vals.append(self._prepare_move_line_vals(quantity=quantity, reserved_quant=reserved_quant))
        return move_line_vals, taken_quantity