def create_resupply_routes(self, supplier_warehouses):
        Route = self.env['stock.route']
        Rule = self.env['stock.rule']

        dummy, output_location = self._get_input_output_locations(self.reception_steps, self.delivery_steps)
        internal_transit_location, external_transit_location = self._get_transit_locations()

        for supplier_wh in supplier_warehouses:
            transit_location = internal_transit_location if supplier_wh.company_id == self.company_id else external_transit_location
            if not transit_location:
                continue
            transit_location.active = True
            output_location = supplier_wh.lot_stock_id if supplier_wh.delivery_steps == 'ship_only' else supplier_wh.wh_output_stock_loc_id
            # Create extra MTO rule (only for 'ship only' because in the other cases MTO rules already exists)
            if supplier_wh.delivery_steps == 'ship_only':
                routing = [self.Routing(output_location, transit_location, supplier_wh.out_type_id, 'pull')]
                mto_vals = supplier_wh._get_global_route_rules_values().get('mto_pull_id')
                values = mto_vals['create_values']
                mto_rule_val = supplier_wh._get_rule_values(routing, values, name_suffix='MTO')
                Rule.create(mto_rule_val[0])

            inter_wh_route = Route.create(self._get_inter_warehouse_route_values(supplier_wh))

            pull_rules_list = supplier_wh._get_supply_pull_rules_values(
                [self.Routing(output_location, transit_location, supplier_wh.out_type_id, 'pull')],
                values={'route_id': inter_wh_route.id, 'location_dest_from_rule': True})
            if supplier_wh.delivery_steps != 'ship_only':
                # Replenish from Output location
                pull_rules_list += supplier_wh._get_supply_pull_rules_values(
                    [self.Routing(supplier_wh.lot_stock_id, output_location, supplier_wh.pick_type_id, 'pull')],
                    values={'route_id': inter_wh_route.id})
            pull_rules_list += self._get_supply_pull_rules_values(
                [self.Routing(transit_location, self.lot_stock_id, self.in_type_id, 'pull')],
                values={'route_id': inter_wh_route.id})
            for pull_rule_vals in pull_rules_list:
                Rule.create(pull_rule_vals)