def _compute_location_dest_id(self):
        customer_loc, __ = self.env['stock.warehouse']._get_partner_locations()
        inter_comp_location = self.env.ref('stock.stock_location_inter_company', raise_if_not_found=False)
        for move in self:
            location_dest = False
            if move.picking_id:
                location_dest = move.picking_id.location_dest_id
            elif move.rule_id.location_dest_from_rule:
                location_dest = move.rule_id.location_dest_id
            elif move.picking_type_id:
                location_dest = move.picking_type_id.default_location_dest_id
            is_move_to_interco_transit = False
            if location_dest:
                is_move_to_interco_transit = location_dest._child_of(customer_loc) and move.location_final_id == inter_comp_location
            if location_dest and move.location_final_id and (move.location_final_id._child_of(location_dest) or is_move_to_interco_transit):
                # Force the location_final as dest in the following cases:
                # - The location_final is a sublocation of destination -> Means we reached the end
                # - The location dest is an out location (i.e. Customers) but the final dest is different (e.g. Inter-Company transfers)
                location_dest = move.location_final_id
            move.location_dest_id = location_dest