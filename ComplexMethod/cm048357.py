def action_create_returns_all(self):
        """ Create a return matching the total delivered quantity and open it.
        """
        self.ensure_one()
        for return_move in self.product_return_moves:
            stock_move = return_move.move_id
            if not stock_move or stock_move.state == 'cancel' or stock_move.location_dest_usage == 'inventory':
                continue
            quantity = stock_move.quantity
            for move in stock_move.move_dest_ids:
                if not move.origin_returned_move_id or move.origin_returned_move_id != stock_move:
                    continue
                quantity -= move.quantity
            quantity = stock_move.product_uom.round(quantity)
            return_move.quantity = quantity
        return self.action_create_returns()