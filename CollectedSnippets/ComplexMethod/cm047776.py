def action_set_qty(self):
        missing_move_vals = []
        problem_tracked_products = self.env['product.product']
        for production in self.mrp_production_ids:
            for line in self.mrp_consumption_warning_line_ids:
                if line.mrp_production_id != production:
                    continue
                for move in production.move_raw_ids:
                    if line.product_id != move.product_id:
                        continue
                    qty_expected = line.product_uom_id._compute_quantity(line.product_expected_qty_uom, move.product_uom)
                    qty_compare_result = move.product_uom.compare(qty_expected, move.quantity)
                    if qty_compare_result != 0:
                        move.quantity = qty_expected
                    # move should be set to picked to correctly consume the product
                    move.picked = True
                    # in case multiple lines with same product => set others to 0 since we have no way to know how to distribute the qty done
                    line.product_expected_qty_uom = 0
                # move was deleted before confirming MO or force deleted somehow
                if not line.product_uom_id.is_zero(line.product_expected_qty_uom):
                    missing_move_vals.append({
                        'product_id': line.product_id.id,
                        'product_uom': line.product_uom_id.id,
                        'product_uom_qty': line.product_expected_qty_uom,
                        'quantity': line.product_expected_qty_uom,
                        'raw_material_production_id': line.mrp_production_id.id,
                        'additional': True,
                        'picked': True,
                    })
        if problem_tracked_products:
            products_list = "".join(f"\n- {product_name}" for product_name in problem_tracked_products.mapped("name"))
            raise UserError(
                _(
                    "Values cannot be set and validated because a Lot/Serial Number needs to be specified for a tracked product that is having its consumed amount increased:%(products)s",
                    products=products_list,
                ),
            )
        if missing_move_vals:
            self.env['stock.move'].create(missing_move_vals)
        return self.action_confirm()