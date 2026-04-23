def _update_standard_price(self, extra_value=None, extra_quantity=None):
        # TODO: Add extra value and extra quantity kwargs to avoid total recomputation
        products_by_cost_method = defaultdict(set)
        for product in self:
            if product.lot_valuated:
                product.sudo().with_context(disable_auto_revaluation=True).standard_price = product.avg_cost
                continue
            products_by_cost_method[product.cost_method].add(product.id)
        for cost_method, product_ids in products_by_cost_method.items():
            products = self.env['product.product'].browse(product_ids)
            if cost_method == 'standard':
                continue
            if cost_method == 'fifo':
                for product in products:
                    qty_available = product._with_valuation_context().qty_available
                    if product.uom_id.compare(qty_available, 0) > 0:
                        product.sudo().with_context(disable_auto_revaluation=True).standard_price = product.total_value / qty_available
                    elif last_in := product._get_last_in():
                        if last_in_price_unit := last_in._get_price_unit():
                            product.sudo().with_context(disable_auto_revaluation=True).standard_price = last_in_price_unit
                continue
            if cost_method == 'average':
                new_standard_price_by_product = self._run_average_batch(force_recompute=True)[0]
                for product in products:
                    if product.id in new_standard_price_by_product:
                        product.with_context(disable_auto_revaluation=True).sudo().standard_price = new_standard_price_by_product[product.id]