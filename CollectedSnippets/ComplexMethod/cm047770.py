def _get_product_available_qty(self, product, **kwargs):
        """ Override of `website_sale_stock` to include free quantities of the product in warehouses
        of in-store delivery method.
        If Click and Collect is enabled, and a warehouse is set on the website:
        - If a in-store pickup location is selected: return the stock at that specific warehouse.
        - If no delivery method is selected: return the maximum between the website's warehouse
        stock and the best stock available among all in-store warehouses.
         """
        free_qty = super()._get_product_available_qty(product, **kwargs)
        if self.warehouse_id and self.sudo().in_store_dm_id:  # If warehouse is set on website.
            order = request and request.cart
            if not order or not order.carrier_id:
                # Check free quantities in the in-store warehouses.
                free_qty = max(free_qty, self._get_max_in_store_product_available_qty(product))
            elif order.carrier_id.delivery_type == 'in_store' and order.pickup_location_data:
                # Get free_qty from the selected location's wh.
                free_qty = product.with_context(warehouse_id=order.warehouse_id.id).free_qty

        return free_qty