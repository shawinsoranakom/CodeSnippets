def write(self, vals):
        moves_to_reassign = self.env['stock.move']
        if vals.get('picking_type_id'):
            picking_type = self.env['stock.picking.type'].browse(vals.get('picking_type_id'))
            for repair in self:
                if repair.state in ('cancel', 'done'):
                    continue
                if picking_type != repair.picking_type_id:
                    repair.name = picking_type.sequence_id.next_by_id()
                    moves_to_reassign |= repair.move_ids
        res = super().write(vals)
        if 'product_id' in vals and self.tracking == 'serial':
            self.write({'product_qty': 1.0})

        for repair in self:
            has_modified_location = any(key in vals for key in MAP_REPAIR_TO_PICKING_LOCATIONS)
            if has_modified_location:
                repair.move_ids._set_repair_locations()
            if 'schedule_date' in vals:
                (repair.move_id + repair.move_ids).filtered(lambda m: m.state not in ('done', 'cancel')).write({'date': repair.schedule_date})
            if 'under_warranty' in vals:
                repair._update_sale_order_line_price()
        if moves_to_reassign:
            moves_to_reassign._do_unreserve()
            moves_to_reassign = moves_to_reassign.filtered(
                lambda move: move.state in ('confirmed', 'partially_available')
                and (move._should_bypass_reservation()
                    or move.picking_type_id.reservation_method == 'at_confirm'
                    or (move.reservation_date and move.reservation_date <= fields.Date.today())))
            moves_to_reassign._action_assign()
        return res