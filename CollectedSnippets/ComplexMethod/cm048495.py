def _sort_locations_by_warehouse(self, rules_and_loc, used_rules, start_locations, ordered_locations, warehouse_id):
        """ We order locations by putting first the locations that are not the destination of others and do it recursively.
        """
        start_locations = start_locations.filtered(lambda l: l.warehouse_id == warehouse_id)
        ordered_locations |= start_locations
        rules_start = []
        for rule in rules_and_loc:
            if rule['source'] in start_locations:
                rules_start.append(rule)
                used_rules |= rule['rule']
        if rules_start:
            rules_start_dest_locations = self.env['stock.location'].concat(*([r['destination'] for r in rules_start]))
            remaining_rules = self.env['stock.rule'].concat(*([r['rule'] for r in rules_and_loc])) - used_rules
            remaining_rules_location = self.env['stock.location']
            for r in rules_and_loc:
                if r['rule'] in remaining_rules:
                    remaining_rules_location |= r['destination']
            start_locations = rules_start_dest_locations - ordered_locations - remaining_rules_location
            ordered_locations = self._sort_locations_by_warehouse(rules_and_loc, used_rules, start_locations, ordered_locations, warehouse_id)
        return ordered_locations