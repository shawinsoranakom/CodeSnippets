def action_split_transfer(self):
        if all(m.product_uom.is_zero(m.quantity) for m in self.move_ids):
            raise UserError(_("%s: Nothing to split. Fill the quantities you want in a new transfer in the done quantities", self.display_name))
        if all(m.product_uom.compare(m.quantity, m.product_uom_qty) == 0 for m in self.move_ids):
            raise UserError(_("%s: Nothing to split, all demand is done. For split you need at least one line not fully fulfilled", self.display_name))
        if any(m.product_uom.compare(m.quantity, m.product_uom_qty) > 0 for m in self.move_ids):
            raise UserError(_("%s: Can't split: quantities done can't be above demand", self.display_name))

        moves = self.move_ids.filtered(lambda m: m.state not in ('done', 'cancel') and m.quantity != 0)
        backorder_moves = moves._create_backorder()
        backorder_moves += self.move_ids.filtered(lambda m: m.quantity == 0)
        self._create_backorder(backorder_moves=backorder_moves)