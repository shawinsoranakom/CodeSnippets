def _merge_moves(self, merge_into=False):
        """ This method will, for each move in `self`, go up in their linked picking and try to
        find in their existing moves a candidate into which we can merge the move.
        :return: Recordset of moves passed to this method. If some of the passed moves were merged
        into another existing one, return this one and not the (now unlinked) original.
        """

        candidate_moves_set = set()
        if not merge_into:
            self._update_candidate_moves_list(candidate_moves_set)
        else:
            candidate_moves_set.add(merge_into | self)

        distinct_fields = (self | self.env['stock.move'].concat(*candidate_moves_set))._prepare_merge_moves_distinct_fields()

        # Move removed after merge
        moves_to_unlink = self.env['stock.move']
        # Moves successfully merged
        merged_moves = self.env['stock.move']
        # Emptied moves
        moves_to_cancel = self.env['stock.move']

        moves_by_neg_key = defaultdict(lambda: self.env['stock.move'])
        # Need to check less fields for negative moves as some might not be set.
        neg_qty_moves = self.filtered(lambda m: m.product_uom.compare(m.product_qty, 0.0) < 0)
        # Detach their picking as they will either get absorbed or create a backorder, so no extra logs will be put in the chatter
        neg_qty_moves.picking_id = False
        excluded_fields = self._prepare_merge_negative_moves_excluded_distinct_fields()
        neg_key = self._merge_move_itemgetter(distinct_fields, excluded_fields)
        price_unit_prec = self.env['decimal.precision'].precision_get('Product Price')

        for candidate_moves in candidate_moves_set:
            # First step find move to merge.
            candidate_moves = candidate_moves.filtered(lambda m: m.state not in ('done', 'cancel', 'draft')) - neg_qty_moves
            for __, g in groupby(candidate_moves, key=self._merge_move_itemgetter(distinct_fields)):
                moves = self.env['stock.move'].concat(*g)
                # Merge all positive moves together
                if len(moves) > 1:
                    # link all move lines to record 0 (the one we will keep).
                    moves.mapped('move_line_ids').write({'move_id': moves[0].id})
                    # merge move data
                    merge_extra = self.env.context.get('merge_extra') and bool(merge_into)
                    moves[0].write(moves.with_context(merge_extra=merge_extra)._merge_moves_fields())
                    # update merged moves dicts
                    moves_to_unlink |= moves[1:]
                    merged_moves |= moves[0]
                # Add the now single positive move to its limited key record
                moves_by_neg_key[neg_key(moves[0])] |= moves[0]

        for neg_move in neg_qty_moves:
            # Check all the candidates that matches the same limited key, and adjust their quantities to absorb negative moves
            for pos_move in moves_by_neg_key.get(neg_key(neg_move), []):
                new_total_value = pos_move.product_qty * pos_move.price_unit + neg_move.product_qty * neg_move.price_unit
                # If quantity can be fully absorbed by a single move, update its quantity and remove the negative move
                if pos_move.product_uom.compare(pos_move.product_uom_qty, abs(neg_move.product_uom_qty)) >= 0:
                    pos_move.product_uom_qty += neg_move.product_uom_qty
                    pos_move.write({
                        'price_unit': float_round(new_total_value / pos_move.product_qty, precision_digits=price_unit_prec) if pos_move.product_qty else 0,
                        'move_dest_ids': [Command.link(m.id) for m in neg_move.mapped('move_dest_ids') if m.location_id == pos_move.location_dest_id],
                        'move_orig_ids': [Command.link(m.id) for m in neg_move.mapped('move_orig_ids') if m.location_dest_id == pos_move.location_id],
                    })
                    merged_moves |= pos_move
                    moves_to_unlink |= neg_move
                    if pos_move.product_uom.is_zero(pos_move.product_uom_qty):
                        moves_to_cancel |= pos_move
                    break
                neg_move.product_uom_qty += pos_move.product_uom_qty
                neg_move.price_unit = float_round(new_total_value / neg_move.product_qty, precision_digits=price_unit_prec)
                pos_move.product_uom_qty = 0
                moves_to_cancel |= pos_move

        # We are using propagate to False in order to not cancel destination moves merged in moves[0]
        (moves_to_unlink | moves_to_cancel)._clean_merged()

        if moves_to_unlink:
            moves_to_unlink._action_cancel()
            moves_to_unlink.sudo().unlink()

        if moves_to_cancel:
            moves_to_cancel.filtered(lambda m: not m.picked)._action_cancel()

        return (self | merged_moves) - moves_to_unlink