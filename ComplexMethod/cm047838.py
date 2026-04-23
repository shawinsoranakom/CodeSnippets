def _get_capacity(self, product, unit, default_capacity=1):
        capacity = self.capacity_ids.sorted(lambda c: (
            not (c.product_id == product and c.product_uom_id == product.uom_id),
            not (not c.product_id and c.product_uom_id == unit),
            not (not c.product_id and c.product_uom_id == product.uom_id),
        ))[:1]
        if capacity and capacity.product_id in [product, self.env['product.product']] and capacity.product_uom_id in [product.uom_id, unit]:
            if float_is_zero(capacity.capacity, 0):
                return (default_capacity, capacity.time_start, capacity.time_stop)
            return (capacity.product_uom_id._compute_quantity(capacity.capacity, unit), capacity.time_start, capacity.time_stop)
        return (default_capacity, self.time_start, self.time_stop)