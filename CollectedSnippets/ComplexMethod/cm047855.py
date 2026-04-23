def action_explode(self):
        """ Explodes pickings """
        # in order to explode a move, we must have a picking_type_id on that move because otherwise the move
        # won't be assigned to a picking and it would be weird to explode a move into several if they aren't
        # all grouped in the same picking.
        moves_ids_to_return = OrderedSet()
        moves_ids_to_unlink = OrderedSet()
        phantom_moves_vals_list = []
        for move in self:
            if (not move.picking_type_id and not (self.env.context.get('is_scrap') or self.env.context.get('skip_picking_assignation'))) or (move.production_id and move.production_id.product_id == move.product_id):
                moves_ids_to_return.add(move.id)
                continue
            bom = self.env['mrp.bom'].sudo()._bom_find(move.product_id, company_id=move.company_id.id, bom_type='phantom')[move.product_id]
            if not bom:
                moves_ids_to_return.add(move.id)
                continue
            if move.product_uom.is_zero(move.product_uom_qty):
                factor = move.product_uom._compute_quantity(move.quantity, bom.product_uom_id) / bom.product_qty
            else:
                factor = move.product_uom._compute_quantity(move.product_uom_qty, bom.product_uom_id) / bom.product_qty
            _dummy, lines = bom.sudo().explode(move.product_id, factor, picking_type=bom.picking_type_id, never_attribute_values=move.never_product_template_attribute_value_ids)
            phantom_moves_vals_list += move._generate_all_phantom_moves(lines)
            # delete the move with original product which is not relevant anymore
            moves_ids_to_unlink.add(move.id)

        if phantom_moves_vals_list:
            phantom_moves = self.env['stock.move'].create(phantom_moves_vals_list)
            phantom_moves._adjust_procure_method()
            moves_ids_to_return |= phantom_moves.action_explode().ids
        move_to_unlink = self.env['stock.move'].browse(moves_ids_to_unlink).sudo()
        move_to_unlink.quantity = 0
        move_to_unlink._action_cancel()
        move_to_unlink.unlink()
        return self.env['stock.move'].browse(moves_ids_to_return)