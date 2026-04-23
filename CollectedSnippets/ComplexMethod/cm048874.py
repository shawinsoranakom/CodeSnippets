def _get_incoming_outgoing_moves_filter(self):
        """ Method to be override: will get incoming moves and outgoing moves.

        :return: Dictionary with incoming moves and outgoing moves
        :rtype: dict
        """
        # The first move created was the one created from the intial rule that started it all.
        sorted_moves = self.move_ids.sorted('id')
        triggering_rule_ids = []
        seen_wh_ids = set()
        seen_bom_id = set()
        for move in sorted_moves:
            if move.bom_line_id.bom_id.id in seen_bom_id:
                triggering_rule_ids.append(move.rule_id.id)
            elif move.warehouse_id.id not in seen_wh_ids:
                triggering_rule_ids.append(move.rule_id.id)
                seen_wh_ids.add(move.warehouse_id.id)
                if move.bom_line_id and move.bom_line_id.bom_id.type == 'phantom':
                    seen_bom_id.add(move.bom_line_id.bom_id.id)

        return {
            'incoming_moves': lambda m: (
                m.state != 'cancel' and m.location_dest_usage != 'inventory'
                and m.rule_id.id in triggering_rule_ids
                and m.location_final_id.usage == 'customer'
                and (not m.origin_returned_move_id or (m.origin_returned_move_id and m.to_refund)
            )),
            'outgoing_moves': lambda m: (
                m.state != 'cancel' and m.location_dest_usage != 'inventory'
                and m.location_id.usage == 'customer' and m.to_refund
            ),
        }