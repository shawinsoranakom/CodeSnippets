def _sort_locations(self, rules_and_loc, warehouses):
        """ We order the locations by setting first the locations of type supplier and manufacture,
            then we add the locations grouped by warehouse and we finish by the locations of type
            customer and the ones that were not added by the sort.
        """
        all_src = self.env['stock.location'].concat(*([r['source'] for r in rules_and_loc]))
        all_dest = self.env['stock.location'].concat(*([r['destination'] for r in rules_and_loc]))
        all_locations = all_src | all_dest
        ordered_locations = self.env['stock.location']
        locations = all_locations.filtered(lambda l: l.usage in ('supplier', 'production'))
        for warehouse_id in warehouses:
            all_warehouse_locations = all_locations.filtered(lambda l: l.warehouse_id == warehouse_id)
            starting_rules = [d for d in rules_and_loc if d['source'] not in all_warehouse_locations]
            if starting_rules:
                start_locations = self.env['stock.location'].concat(*([r['destination'] for r in starting_rules]))
            else:
                starting_rules = [d for d in rules_and_loc if d['source'] not in all_dest]
                start_locations = self.env['stock.location'].concat(*([r['source'] for r in starting_rules]))
            used_rules = self.env['stock.rule']
            locations |= self._sort_locations_by_warehouse(rules_and_loc, used_rules, start_locations, ordered_locations, warehouse_id)
            if any(location not in locations for location in all_warehouse_locations):
                remaining_locations = self.env['stock.location'].concat(*([r['source'] for r in rules_and_loc])).filtered(lambda l: l not in locations)
                locations |= self._sort_locations_by_warehouse(rules_and_loc, used_rules, remaining_locations, ordered_locations, warehouse_id)
        locations |= all_locations.filtered(lambda l: l.usage in ('customer'))
        locations |= all_locations.filtered(lambda l: l not in locations)
        return locations