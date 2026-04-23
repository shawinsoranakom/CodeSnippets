def _action_confirm(self, merge=True, merge_into=False, create_proc=True):
        """ Confirms stock move or put it in waiting if it's linked to another move.
        :param: merge: According to this boolean, a newly confirmed move will be merged
        in another move of the same picking sharing its characteristics.
        """
        # Use OrderedSet of id (instead of recordset + |= ) for performance
        move_create_proc, move_to_confirm, move_waiting = OrderedSet(), OrderedSet(), OrderedSet()
        to_assign = defaultdict(OrderedSet)
        for move in self:
            if move.state != 'draft':
                continue
            # if the move is preceded, then it's waiting (if preceding move is done, then action_assign has been called already and its state is already available)
            if move.move_orig_ids:
                move_waiting.add(move.id)
            elif move.procure_method == 'make_to_order':
                move_waiting.add(move.id)
                if create_proc:
                    move_create_proc.add(move.id)
            elif move.rule_id and move.rule_id.procure_method == 'mts_else_mto':
                move_to_confirm.add(move.id)
                if create_proc:
                    move_create_proc.add(move.id)
            else:
                move_to_confirm.add(move.id)
            if move._should_be_assigned():
                key = (frozenset(move.reference_ids.ids), move.location_id.id, move.location_dest_id.id)
                to_assign[key].add(move.id)

        # create procurements for make to order moves
        procurement_requests = []
        move_create_proc = self.browse(move_create_proc)
        quantities = move_create_proc._prepare_procurement_qty()
        for move, quantity in zip(move_create_proc, quantities):
            values = move._prepare_procurement_values()
            origin = move._prepare_procurement_origin()
            procurement_requests.append(self.env['stock.rule'].Procurement(
                move.product_id, quantity, move.product_uom,
                move.location_id, move.rule_id and move.rule_id.name or "/",
                origin, move.company_id, values))
        self.env['stock.rule'].run(procurement_requests, raise_user_error=not self.env.context.get('from_orderpoint'))

        move_to_confirm, move_waiting = self.browse(move_to_confirm).filtered(lambda m: m.state != 'cancel'), self.browse(move_waiting).filtered(lambda m: m.state != 'cancel')
        move_to_confirm.write({'state': 'confirmed'})
        move_waiting.write({'state': 'waiting'})
        # procure_method sometimes changes with certain workflows so just in case, apply to all moves
        (move_to_confirm | move_waiting).filtered(lambda m: m.picking_type_id.reservation_method == 'at_confirm')\
            .write({'reservation_date': fields.Date.today()})

        # assign picking in batch for all confirmed move that share the same details
        for moves_ids in to_assign.values():
            self.browse(moves_ids).with_context(clean_context(self.env.context))._assign_picking()

        self._check_company()
        moves = self
        if merge:
            moves = self._merge_moves(merge_into=merge_into)

        neg_r_moves = moves.filtered(lambda move: move.product_uom.compare(move.product_uom_qty, 0) < 0)

        # Push remaining quantities to next step
        neg_to_push = neg_r_moves.filtered(lambda move: move.location_final_id and move.location_dest_id != move.location_final_id)
        new_push_moves = self.env['stock.move']
        if neg_to_push:
            new_push_moves = neg_to_push._push_apply()

        # Transform remaining move in returns in case of negative initial demand
        for move in neg_r_moves:
            move.location_id, move.location_dest_id, move.location_final_id = move.location_dest_id, move.location_id, move.location_id
            orig_move_ids, dest_move_ids = [], []
            for m in move.move_orig_ids | move.move_dest_ids:
                from_loc, to_loc = m.location_id, m.location_dest_id
                if m.product_uom.compare(m.product_uom_qty, 0) < 0:
                    from_loc, to_loc = to_loc, from_loc
                if to_loc == move.location_id:
                    orig_move_ids += m.ids
                elif move.location_dest_id == from_loc:
                    dest_move_ids += m.ids
            move.move_orig_ids, move.move_dest_ids = [Command.set(orig_move_ids)], [Command.set(dest_move_ids)]
            move.product_uom_qty *= -1
            if move.picking_type_id.return_picking_type_id:
                move.picking_type_id = move.picking_type_id.return_picking_type_id
            # We are returning some products, we must take them in the source location
            move.procure_method = 'make_to_stock'
        neg_r_moves._assign_picking()

        # call `_action_assign` on every confirmed move which location_id bypasses the reservation + those expected to be auto-assigned
        moves.filtered(lambda move: move.state in ('confirmed', 'partially_available')
                       and (move._should_bypass_reservation() or move._should_assign_at_confirm()))\
             ._action_assign()
        if new_push_moves:
            neg_push_moves = new_push_moves.filtered(lambda sm: sm.product_uom.compare(sm.product_uom_qty, 0) < 0)
            (new_push_moves - neg_push_moves).sudo()._action_confirm()
            # Negative moves do not have any picking, so we should try to merge it with their siblings
            neg_push_moves._action_confirm(merge_into=neg_push_moves.move_orig_ids.move_dest_ids)
        return moves