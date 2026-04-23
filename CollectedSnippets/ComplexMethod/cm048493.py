def _get_report_values(self, docids, data=None):
        # Overriding data values here since used also in _get_routes.
        data['product_id'] = data.get('product_id', docids)
        data['warehouse_ids'] = data.get('warehouse_ids', [])

        product = self.env['product.product'].browse(data['product_id'])
        warehouses = self.env['stock.warehouse'].browse(data['warehouse_ids'])

        routes = self._get_routes(data)

        # Some routes don't have a warehouse_id but contain rules of different warehouses,
        # we filter here the ones we want to display and build for each one a dict containing the rule,
        # their source and destination location.
        relevant_rules = routes.mapped('rule_ids').filtered(lambda r: not r.warehouse_id or r.warehouse_id in warehouses)
        rules_and_loc = []
        for rule in relevant_rules:
            rules_and_loc.append(self._get_rule_loc(rule, product))

        locations = self._sort_locations(rules_and_loc, warehouses)
        reordering_rules = self.env['stock.warehouse.orderpoint'].search([('product_id', '=', product.id)])
        locations |= reordering_rules.mapped('location_id').filtered(lambda l: l not in locations)
        locations_names = locations.mapped('display_name')
        # Here we handle reordering rules and putaway strategies by creating the header_lines dict. This dict is indexed
        # by location_id and contains itself another dict with the relevant reordering rules and putaway strategies.
        header_lines = {}
        for location in locations:
            # TODO: group the RR by location_id to avoid a filtered at each loop
            rr = reordering_rules.filtered(lambda r: r.location_id.id == location.id)
            putaways = product.putaway_rule_ids.filtered(lambda p: p.location_in_id.id == location.id)
            if putaways or rr:
                header_lines[location.id] = {'putaway': [], 'orderpoint': []}
                for putaway in putaways:
                    header_lines[location.id]['putaway'].append(putaway)
                for r in rr:
                    header_lines[location.id]['orderpoint'].append(r)
        route_lines = []
        colors = self._get_route_colors()
        for color_index, route in enumerate(routes):
            rules_to_display = route.rule_ids & relevant_rules
            if rules_to_display:
                route_color = colors[color_index % len(colors)]
                color_index = color_index + 1
                for rule in rules_to_display:
                    rule_loc = [r for r in rules_and_loc if r['rule'] == rule][0]
                    res = [[] for _loc in locations_names]
                    idx = locations_names.index(rule_loc['destination'].display_name)
                    tpl = (rule, 'destination', route_color, )
                    res[idx] = tpl
                    idx = locations_names.index(rule_loc['source'].display_name)
                    tpl = (rule, 'origin', route_color, )
                    res[idx] = tpl
                    route_lines.append(res)
        return {
            'docs': product,
            'locations': locations,
            'header_lines': header_lines,
            'route_lines': route_lines,
            'is_rtl': self.env['res.lang']._lang_get(self.env.user.lang).direction == 'rtl',
        }