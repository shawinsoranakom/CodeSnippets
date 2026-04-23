def _set_lot_ids(self):
        for move in self:
            if move.state == 'assigned' and all(ml.lot_id in move.lot_ids for ml in move.move_line_ids):
                continue
            move_lines_commands = []
            mls = move.move_line_ids
            mls_with_lots = mls.filtered(lambda ml: ml.lot_id)
            mls_without_lots = (mls - mls_with_lots)
            for ml in mls_with_lots:
                if ml.quantity and ml.lot_id not in move.lot_ids:
                    move_lines_commands.append((2, ml.id))
            ls = move.move_line_ids.lot_id
            for lot in move.lot_ids:
                if lot not in ls:
                    if mls_without_lots[:1]:  # Updates an existing line without serial number.
                        move_line = mls_without_lots[:1]
                        move_lines_commands.append(Command.update(move_line.id, {
                            'lot_id': lot.id,
                            'product_uom_id': move.product_id.uom_id.id if move.product_id.tracking == 'serial' else move.product_uom.id,
                            'quantity': 1 if move.product_id.tracking == 'serial' else move.quantity,
                        }))
                        mls_without_lots -= move_line
                    else:  # No line without serial number, creates a new one.
                        reserved_quants = self.env['stock.quant'].with_context(packaging_uom_id=move.packaging_uom_id)._get_reserve_quantity(move.product_id, move.location_id, 1.0, lot_id=lot)
                        if reserved_quants and reserved_quants[0][0].lot_id:
                            move_line_vals = self._prepare_move_line_vals(quantity=0, reserved_quant=reserved_quants[0][0])
                        else:
                            move_line_vals = self._prepare_move_line_vals(quantity=0)
                            move_line_vals['lot_id'] = lot.id
                        move_line_vals['product_uom_id'] = move.product_id.uom_id.id
                        move_line_vals['quantity'] = 1
                        move_lines_commands.append((0, 0, move_line_vals))
                else:
                    move_line = move.move_line_ids.filtered(lambda line: line.lot_id.id == lot.id)
                    move_line.quantity = 1
            move.write({'move_line_ids': move_lines_commands})