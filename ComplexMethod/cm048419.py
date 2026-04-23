def _push_prepare_move_copy_values(self, move_to_copy, new_date):
        company_id = self.company_id.id
        copied_quantity = move_to_copy.quantity
        final_location_id = False
        location_dest_id = self.location_dest_id.id
        if move_to_copy.location_final_id and not move_to_copy.location_dest_id._child_of(move_to_copy.location_final_id):
            final_location_id = move_to_copy.location_final_id.id
        if move_to_copy.location_final_id and move_to_copy.location_final_id._child_of(self.location_dest_id):
            location_dest_id = move_to_copy.location_final_id.id
        if move_to_copy.product_uom.compare(move_to_copy.product_uom_qty, 0) < 0:
            copied_quantity = move_to_copy.product_uom_qty
        if not company_id:
            company_id = self.sudo().warehouse_id and self.sudo().warehouse_id.company_id.id or self.sudo().picking_type_id.warehouse_id.company_id.id
        new_move_vals = {
            'product_uom_qty': copied_quantity,
            'origin': move_to_copy.origin or move_to_copy.picking_id.name or "/",
            'location_id': move_to_copy.location_dest_id.id,
            'location_dest_id': location_dest_id,
            'location_final_id': final_location_id,
            'rule_id': self.id,
            'date': new_date,
            'date_deadline': move_to_copy.date_deadline,
            'company_id': company_id,
            'picking_id': False,
            'picking_type_id': self.picking_type_id.id,
            'propagate_cancel': self.propagate_cancel,
            'warehouse_id': self.warehouse_id.id or move_to_copy.location_dest_id.warehouse_id.id,
            'procure_method': 'make_to_order',
        }
        return new_move_vals