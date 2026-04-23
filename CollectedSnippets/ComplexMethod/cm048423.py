def _search_rule(self, route_ids, packaging_uom_id, product_id, warehouse_id, domain):
        """ First find a rule among the ones defined on the procurement
        group, then try on the routes defined for the product, finally fallback
        on the default behavior
        """
        Rule = self.env['stock.rule']
        res = self.env['stock.rule']
        domain = Domain(domain)
        if warehouse_id:
            domain &= Domain('warehouse_id', 'in', [False, warehouse_id.id])
        domain = domain.optimize(Rule)
        if route_ids:
            res = Rule.search(Domain('route_id', 'in', route_ids.ids) & domain, order='route_sequence, sequence', limit=1)
        if not res and packaging_uom_id:
            packaging_routes = packaging_uom_id.package_type_id.route_ids
            if packaging_routes:
                res = Rule.search(Domain('route_id', 'in', packaging_routes.ids) & domain, order='route_sequence, sequence', limit=1)
        if not res:
            product_routes = product_id.route_ids | product_id.categ_id.total_route_ids
            if product_routes:
                res = Rule.search(Domain('route_id', 'in', product_routes.ids) & domain, order='route_sequence, sequence', limit=1)
        if not res and warehouse_id:
            warehouse_routes = warehouse_id.route_ids
            if warehouse_routes:
                res = Rule.search(Domain('route_id', 'in', warehouse_routes.ids) & domain, order='route_sequence, sequence', limit=1)
        return res