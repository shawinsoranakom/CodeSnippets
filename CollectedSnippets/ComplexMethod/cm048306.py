def _compute_is_mto(self):
        super(SaleOrderLine, self)._compute_is_mto()
        for line in self:
            if not line.display_qty_widget or line.is_mto:
                continue
            product_routes = line.route_ids or (line.product_id.route_ids + line.product_id.categ_id.total_route_ids)
            for pull_rule in product_routes.mapped('rule_ids'):
                if pull_rule.picking_type_id.sudo().default_location_src_id.usage == 'supplier' and\
                        pull_rule.picking_type_id.sudo().default_location_dest_id.usage == 'customer':
                    line.is_mto = True
                    break