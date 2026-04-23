def _create_or_update_route(self):
        """ Create or update the warehouse's routes.
        _get_routes_values method return a dict with:
            - route field name (e.g: delivery_route_id).
            - field that trigger an update on the route (key 'depends').
            - routing_key used in order to find rules contained in the route.
            - create values.
            - update values when a field in depends is modified.
            - rules default values.
        This method do an iteration on each route returned and update/create
        them. In order to update the rules contained in the route it will
        use the get_rules_dict that return a dict:
            - a receptions/delivery,... step value as key (e.g  'pick_ship')
            - a list of routing object that represents the rules needed to
            fullfil the pupose of the route.
        The routing_key from _get_routes_values is match with the get_rules_dict
        key in order to create/update the rules in the route
        (_find_existing_rule_or_create method is responsible for this part).
        """
        # Create routes and active/create their related rules.
        self.ensure_one()
        routes = []
        rules_dict = self.get_rules_dict()
        for route_field, route_data in self._get_routes_values().items():
            # If the route exists update it
            if self[route_field]:
                route = self[route_field]
                if 'route_update_values' in route_data:
                    route.write(route_data['route_update_values'])
                route.rule_ids.write({'active': False})
            # Create the route
            else:
                if 'route_update_values' in route_data:
                    route_data['route_create_values'].update(route_data['route_update_values'])
                route = self.env['stock.route'].create(route_data['route_create_values'])
                self[route_field] = route
            # Get rules needed for the route
            routing_key = route_data.get('routing_key')
            rules = rules_dict[self.id][routing_key]
            if 'rules_values' in route_data:
                route_data['rules_values'].update({'route_id': route.id})
            else:
                route_data['rules_values'] = {'route_id': route.id}
            rules_list = self._get_rule_values(
                rules, values=route_data['rules_values'])
            # Create/Active rules
            self._find_existing_rule_or_create(rules_list)
            if route_data['route_create_values'].get('warehouse_selectable', False) or route_data['route_update_values'].get('warehouse_selectable', False):
                routes.append(self[route_field])
        return {
            'route_ids': [(4, route.id) for route in routes],
        }