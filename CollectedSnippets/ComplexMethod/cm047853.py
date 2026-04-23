def write(self, vals):
        if 'product_id' in vals:
            move_to_unlink = self.filtered(lambda m: m.product_id.id != vals.get('product_id'))
            other_move = self - move_to_unlink
            if move_to_unlink.production_id and move_to_unlink.state not in ['draft', 'cancel', 'done']:
                moves_data = move_to_unlink.copy_data()
                for move_data in moves_data:
                    move_data.update({'product_id': vals.get('product_id')})
                updated_product_move = self.create(moves_data)
                updated_product_move._action_confirm()
                move_to_unlink.unlink()
                self = other_move + updated_product_move
        moves_to_update = False
        if self.env.context.get('force_manual_consumption') and 'quantity' in vals:
            moves_to_update = self.filtered(lambda move: move.product_uom_qty != vals['quantity'])
        if 'product_uom_qty' in vals and 'move_line_ids' in vals:
            # first update lines then product_uom_qty as the later will unreserve
            # so possibly unlink lines
            move_line_vals = vals.pop('move_line_ids')
            super().write({'move_line_ids': move_line_vals})
        old_demand = {move.id: move.product_uom_qty for move in self}
        res = super().write(vals)
        if moves_to_update:
            moves_to_update.write({'manual_consumption': True, 'picked': True})
        if 'product_uom_qty' in vals and not self.env.context.get('no_procurement', False):
            # when updating consumed qty need to update related pickings
            # context no_procurement means we don't want the qty update to modify stock i.e create new pickings
            # ex. when spliting MO to backorders we don't want to move qty from pre prod to stock in 2/3 step config
            self.filtered(lambda m: m.raw_material_production_id.state in ('confirmed', 'progress', 'to_close'))._run_procurement(old_demand)
        return res