def _get_outgoing_incoming_moves(self):
        outgoing_moves = self.env['stock.move']
        incoming_moves = self.env['stock.move']

        for move in self.move_ids.filtered(lambda r: r.state != 'cancel' and r.location_dest_usage != 'inventory' and self.product_id == r.product_id):
            if move._is_purchase_return() and (move.to_refund or not move.origin_returned_move_id):
                outgoing_moves |= move
            elif move.location_dest_id.usage != "supplier":
                if not move.origin_returned_move_id or (move.origin_returned_move_id and move.to_refund):
                    incoming_moves |= move

        return outgoing_moves, incoming_moves