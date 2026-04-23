def _get_outgoing_incoming_moves(self, strict=True):
        """ Return the outgoing and incoming moves of the sale order line.
            @param strict: If True, only consider the moves that are strictly delivered to the customer (old behavior).
                           If False, consider the moves that were created through the initial rule of the delivery route,
                           to support the new push mechanism.
        """
        outgoing_moves_ids = set()
        incoming_moves_ids = set()

        moves = self.move_ids.filtered(lambda r: r.state != 'cancel' and r.location_dest_usage != 'inventory' and self.product_id == r.product_id)
        if moves and not strict:
            # The first move created was the one created from the intial rule that started it all.
            sorted_moves = moves.sorted('id')
            triggering_rule_ids = []
            seen_wh_ids = set()
            for move in sorted_moves:
                if move.warehouse_id.id not in seen_wh_ids and move.rule_id:
                    triggering_rule_ids.append(move.rule_id.id)
                    seen_wh_ids.add(move.warehouse_id.id)
        if self.env.context.get('accrual_entry_date'):
            accrual_date = fields.Date.from_string(self.env.context['accrual_entry_date'])
            moves = moves.filtered(lambda r: fields.Date.context_today(r, r.date) <= accrual_date)

        for move in moves:
            if not move._is_dropshipped_returned() and (
                (strict and move.location_dest_id._is_outgoing()) or (
                not strict and move.rule_id.id in triggering_rule_ids and
                (move.location_final_id or move.location_dest_id)._is_outgoing()
            )):
                if not move.origin_returned_move_id or (move.origin_returned_move_id and move.to_refund):
                    outgoing_moves_ids.add(move.id)
            elif move.to_refund and (
                (strict and move._is_incoming() or move.location_id._is_outgoing()) or (
                not strict and move.rule_id.id in triggering_rule_ids and
                (move.location_final_id or move.location_dest_id).usage == 'internal'
            )):
                incoming_moves_ids.add(move.id)

        return self.env['stock.move'].browse(outgoing_moves_ids), self.env['stock.move'].browse(incoming_moves_ids)