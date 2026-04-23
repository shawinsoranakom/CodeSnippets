def action_assign(self, move_ids, qtys, in_ids):
        """ Assign picking move(s) [i.e. link] to other moves (i.e. make them MTO)
        :param move_id ids: the ids of the moves to make MTO
        :param qtys list: the quantities that are being assigned to the move_ids (in same order as move_ids)
        :param in_ids ids: the ids of the moves that are to be assigned to move_ids
        """
        outs = self.env['stock.move'].browse(move_ids)
        # Split outs with only part of demand assigned to prevent reservation problems later on.
        # We do this first so we can create their split moves in batch
        out_to_new_out = OrderedDict()
        new_move_vals = []
        for out, qty_to_link in zip(outs, qtys):
            if out.product_id.uom_id.compare(out.product_qty, qty_to_link) == 1:
                new_move = out._split(out.product_qty - qty_to_link)
                if new_move:
                    new_move[0]['reservation_date'] = out.reservation_date
                new_move_vals += new_move
                out_to_new_out[out.id] = self.env['stock.move']
        new_outs = self.env['stock.move'].create(new_move_vals)
        # don't do action confirm to avoid creating additional unintentional reservations
        new_outs.write({'state': 'confirmed'})
        for i, k in enumerate(out_to_new_out.keys()):
            out_to_new_out[k] = new_outs[i]

        for out, qty_to_link, ins in zip(outs, qtys, in_ids):
            potential_ins = self.env['stock.move'].browse(ins)
            if out.id in out_to_new_out:
                new_out = out_to_new_out[out.id]
                if potential_ins[0].state != 'done' and out.quantity:
                    # let's assume if 1 of the potential_ins isn't done, then none of them are => we are only assigning the not-reserved
                    # qty and the new move should have all existing reserved quants (i.e. move lines) assigned to it
                    out.move_line_ids.move_id = new_out
                elif potential_ins[0].state == 'done' and out.quantity > qty_to_link:
                    # let's assume if 1 of the potential_ins is done, then all of them are => we can link them to already reserved moves, but we
                    # need to make sure the reserved qtys still match the demand amount the move (we're assigning).
                    out.move_line_ids.move_id = new_out
                    assigned_amount = 0
                    matching_locations = potential_ins.location_dest_id
                    for move_line_id in new_out.move_line_ids.sorted(lambda ml: ml.location_id not in matching_locations):
                        if assigned_amount + move_line_id.quantity_product_uom > qty_to_link:
                            new_move_line = move_line_id.copy({'quantity': 0})
                            new_move_line.quantity = move_line_id.quantity
                            move_line_id.quantity = out.product_id.uom_id._compute_quantity(qty_to_link - assigned_amount, out.product_uom, rounding_method='HALF-UP')
                            new_move_line.quantity -= out.product_id.uom_id._compute_quantity(move_line_id.quantity_product_uom, out.product_uom, rounding_method='HALF-UP')
                        move_line_id.move_id = out
                        assigned_amount += move_line_id.quantity_product_uom
                        if out.product_id.uom_id.compare(assigned_amount, qty_to_link) == 0:
                            break

            for in_move in reversed(potential_ins):
                move_quantity = in_move.product_qty or in_move.product_uom._compute_quantity(in_move.quantity, in_move.product_id.uom_id, rounding_method='HALF-UP')
                quantity_remaining = move_quantity - sum(in_move.move_dest_ids.mapped('product_qty'))
                if in_move.product_id != out.product_id or in_move.product_id.uom_id.compare(0, quantity_remaining) >= 0:
                    # in move is already completely linked (e.g. during another assign click) => don't count it again
                    potential_ins = potential_ins[1:]
                    continue

                linked_qty = min(move_quantity, qty_to_link)
                in_move.move_dest_ids |= out
                self._action_assign(in_move, out)
                out.procure_method = 'make_to_order'
                quantity_remaining -= linked_qty
                qty_to_link -= linked_qty
                if out.product_id.uom_id.is_zero(qty_to_link):
                    break  # we have satistfied the qty_to_link

        (outs | new_outs)._recompute_state()

        # always try to auto-assign to prevent another move from reserving the quant if incoming move is done
        self.env['stock.move'].browse(move_ids)._action_assign()