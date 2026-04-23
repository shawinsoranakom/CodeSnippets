def _prepare_procurement_qty(self):
        quantities = []
        mtso_products_by_locations = defaultdict(list)
        mtso_moves = set()
        for move in self:
            if move.rule_id and move.rule_id.procure_method == 'mts_else_mto':
                mtso_moves.add(move.id)
                mtso_products_by_locations[move.location_id].append(move.product_id.id)

        # Get the forecasted quantity for the `mts_else_mto` procurement.
        forecasted_qties_by_loc = {}
        for location, product_ids in mtso_products_by_locations.items():
            if location.should_bypass_reservation():
                continue
            products = self.env['product.product'].browse(product_ids).with_context(location=location.id)
            forecasted_qties_by_loc[location] = {product.id: product.free_qty for product in products}
        for move in self:
            if move.id not in mtso_moves or move.product_id.uom_id.compare(move.product_qty, 0) <= 0:
                quantities.append(move.product_uom_qty)
                continue

            if move._should_bypass_reservation():
                quantities.append(move.product_uom_qty)
                continue

            free_qty = max(forecasted_qties_by_loc[move.location_id][move.product_id.id], 0)
            quantity = max(move.product_qty - free_qty, 0)
            product_uom_qty = move.product_id.uom_id._compute_quantity(quantity, move.product_uom, rounding_method='HALF-UP')
            quantities.append(product_uom_qty)
            forecasted_qties_by_loc[move.location_id][move.product_id.id] -= min(move.product_qty, free_qty)

        return quantities