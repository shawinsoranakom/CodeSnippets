def _get_rule_values(self, route_values, values=None, name_suffix=''):
        first_rule = True
        rules_list = []
        for routing in route_values:
            route_rule_values = {
                'name': self._format_rulename(routing.from_loc, routing.dest_loc, name_suffix),
                'location_src_id': routing.from_loc.id,
                'location_dest_id': routing.dest_loc.id,
                'action': routing.action,
                'auto': 'manual',
                'picking_type_id': routing.picking_type.id,
                'procure_method': first_rule and 'make_to_stock' or 'make_to_order',
                'warehouse_id': self.id,
                'company_id': self.company_id.id,
            }
            route_rule_values.update(values or {})
            rules_list.append(route_rule_values)
            first_rule = False
        if values and values.get('propagate_cancel') and rules_list:
            # In case of rules chain with cancel propagation set, we need to stop
            # the cancellation for the last step in order to avoid cancelling
            # any other move after the chain.
            # Example: In the following flow:
            # Input -> Quality check -> Stock -> Customer
            # We want that cancelling I->GC cancel QC -> S but not S -> C
            # which means:
            # Input -> Quality check should have propagate_cancel = True
            # Quality check -> Stock should have propagate_cancel = False
            rules_list[-1]['propagate_cancel'] = False
        return rules_list