def _check_can_be_used(self, product, quantity=0, package=None, location_qty=0):
        """Check if product/package can be stored in the location. Quantity
        should in the default uom of product, it's only used when no package is
        specified."""
        self.ensure_one()
        if self.storage_category_id:
            forecast_weight = self._get_weight(self.env.context.get('exclude_sml_ids', set()))[self]['forecast_weight']
            # check if enough space
            if package and package.package_type_id:
                # check weight
                package_smls = self.env['stock.move.line'].search([('result_package_id', '=', package.id), ('state', 'not in', ['done', 'cancel'])])
                if self.storage_category_id.max_weight < forecast_weight + sum(package_smls.mapped(lambda sml: sml.quantity_product_uom * sml.product_id.weight)):
                    return False
                # check if enough space
                package_capacity = self.storage_category_id.package_capacity_ids.filtered(lambda pc: pc.package_type_id == package.package_type_id)
                if package_capacity and location_qty >= package_capacity.quantity:
                    return False
            else:
                # check weight
                if self.storage_category_id.max_weight < forecast_weight + product.weight * quantity:
                    return False
                product_capacity = self.storage_category_id.product_capacity_ids.filtered(lambda pc: pc.product_id == product)
                # To handle new line without quantity in order to avoid suggesting a location already full
                if product_capacity and location_qty >= product_capacity.quantity:
                    return False
                if product_capacity and quantity + location_qty > product_capacity.quantity:
                    return False
            positive_quant = self.quant_ids.filtered(lambda q: q.product_id.uom_id.compare(q.quantity, 0) > 0)
            # check if only allow new product when empty
            if self.storage_category_id.allow_new_product == "empty" and positive_quant:
                return False
            # check if only allow same product
            if self.storage_category_id.allow_new_product == "same":
                # In case it's a package, `product` is not defined, so try to get
                # the package products from the context
                product = product or self.env.context.get('products')
                if (positive_quant and positive_quant.product_id != product) or len(product) > 1:
                    return False
                if self.env['stock.move.line'].search_count([
                    ('product_id', '!=', product.id),
                    ('state', 'not in', ('done', 'cancel')),
                    ('location_dest_id', '=', self.id),
                ], limit=1):
                    return False
        return True