def _get_rule(self, product_id, location_id, values):
        """ Find a pull rule for the location_id, fallback on the parent
        locations if it could not be found.
        """
        result = self.env['stock.rule']
        if not location_id:
            return result
        locations = location_id
        # Get the location hierarchy, starting from location_id up to its root location.
        while locations[-1].location_id:
            locations |= locations[-1].location_id
        domain = self._get_rule_domain(locations, values)
        # Get a mapping (location_id, route_id) -> warehouse_id -> rule_id
        rule_dict = self._search_rule_for_warehouses(
            values.get("route_ids", False),
            values.get("packaging_uom_id", False),
            product_id,
            values.get("warehouse_id", locations.warehouse_id),
            domain,
        )

        def extract_rule(rule_dict, route_ids, warehouse_id, location_dest_id):
            rule = self.env['stock.rule']
            for route_id in sorted(route_ids, key=lambda r: (r not in product_id.route_ids, r.sequence)):
                sub_dict = rule_dict.get((location_dest_id.id, route_id.id))
                if not sub_dict:
                    continue
                if not warehouse_id:
                    rule = sub_dict[next(iter(sub_dict))]
                else:
                    rule = sub_dict.get(warehouse_id.id)
                    rule = rule or sub_dict[False]
                if rule:
                    break
            return rule

        def get_rule_for_routes(rule_dict, route_ids, packaging_uom_id, product_id, warehouse_id, location_dest_id):
            res = self.env['stock.rule']
            if route_ids:
                res = extract_rule(rule_dict, route_ids, warehouse_id, location_dest_id)
            if not res and packaging_uom_id:
                res = extract_rule(rule_dict, packaging_uom_id.package_type_id.route_ids, warehouse_id, location_dest_id)
            if not res:
                res = extract_rule(rule_dict, product_id.route_ids | product_id.categ_id.total_route_ids, warehouse_id, location_dest_id)
            if not res and warehouse_id:
                res = extract_rule(rule_dict, warehouse_id.route_ids, warehouse_id, location_dest_id)
            return res

        location = location_id
        # Go through the location hierarchy again, this time breaking at the first valid stock.rule found
        # in rules_by_location.
        inter_comp_location_checked = False
        while (not result) and location:
            candidate_locations = location
            if not inter_comp_location_checked and self._check_intercomp_location(location):
                # Add the intercomp location to candidate_locations as the intercomp domain was added
                # above in the call to _get_rule_domain.
                inter_comp_location = self.env.ref('stock.stock_location_customers', raise_if_not_found=False)
                candidate_locations |= inter_comp_location
                inter_comp_location_checked = True
            for candidate_location in candidate_locations:
                result = get_rule_for_routes(
                    rule_dict,
                    values.get("route_ids", self.env['stock.route']),
                    values.get("packaging_uom_id", self.env['uom.uom']),
                    product_id,
                    values.get("warehouse_id", candidate_location.warehouse_id),
                    candidate_location,
                )
                if result:
                    break
            else:
                location = location.location_id
        return result