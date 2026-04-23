def _compute_is_mto(self):
        """ Verify the route of the product based on the warehouse
            set 'is_available' at True if the product availability in stock does
            not need to be verified, which is the case in MTO, Drop-Shipping
        """
        self.is_mto = False
        for line in self:
            if not line.display_qty_widget:
                continue
            product = line.product_id
            product_routes = line.route_ids or (product.route_ids + product.categ_id.total_route_ids)

            # Check MTO
            mto_route = line.warehouse_id.mto_pull_id.route_id
            if not mto_route:
                try:
                    mto_route = self.env['stock.warehouse']._find_or_create_global_route('stock.route_warehouse0_mto', _('Replenish on Order (MTO)'), create=False)
                except UserError:
                    # if route MTO not found in ir_model_data, we treat the product as in MTS
                    pass

            if mto_route and mto_route in product_routes:
                line.is_mto = True
            else:
                line.is_mto = False