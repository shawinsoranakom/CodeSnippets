def _get_consumption_issues(self):
        """Compare the quantity consumed of the components, the expected quantity
        on the BoM and the consumption parameter on the order.

        :return: list of tuples (order_id, product_id, consumed_qty, expected_qty) where the
            consumption isn't honored. order_id and product_id are recordset of mrp.production
            and product.product respectively
        :rtype: list
        """
        issues = []
        if self.env.context.get('skip_consumption', False):
            return issues
        for order in self:
            if order.consumption == 'flexible' or not order.bom_id or not order.bom_id.bom_line_ids:
                continue
            expected_move_values = order._get_moves_raw_values()
            expected_qty_by_product = defaultdict(float)
            for move_values in expected_move_values:
                move_product = self.env['product.product'].browse(move_values['product_id'])
                move_uom = self.env['uom.uom'].browse(move_values['product_uom'])
                move_product_qty = move_uom._compute_quantity(move_values['product_uom_qty'], move_product.uom_id)
                expected_qty_by_product[move_product] += move_product_qty * order.qty_producing / order.product_qty

            done_qty_by_product = defaultdict(float)
            for move in order.move_raw_ids:
                quantity = move.product_uom._compute_quantity(move._get_picked_quantity(), move.product_id.uom_id)
                # extra lines with non-zero qty picked
                if move.product_id not in expected_qty_by_product and move.picked and not move.product_id.uom_id.is_zero(quantity):
                    issues.append((order, move.product_id, quantity, 0.0))
                    continue
                done_qty_by_product[move.product_id] += quantity if move.picked else 0.0

            # origin lines from bom with different qty
            for product, qty_to_consume in expected_qty_by_product.items():
                quantity = done_qty_by_product.get(product, 0.0)
                if product.uom_id.compare(qty_to_consume, quantity) != 0:
                    issues.append((order, product, quantity, qty_to_consume))

        return issues