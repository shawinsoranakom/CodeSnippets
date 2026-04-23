def _run_fifo(self, quantity, lot=None, at_date=None, location=None):
        """ Returns the value for the next outgoing product base on the qty give as argument."""
        self.ensure_one()
        if self.uom_id.compare(quantity, 0) <= 0:
            if at_date:
                last_in = self._get_last_in(at_date)
                return quantity * (last_in._get_price_unit() if last_in else self.standard_price)
            return quantity * self.standard_price
        external_location = location and location.is_valued_external

        fifo_cost = 0
        fifo_stack, qty_on_first_move = self._run_fifo_get_stack(lot=lot, at_date=at_date, location=location)
        last_move = False
        # Going up to get the quantity in the argument
        while quantity > 0 and fifo_stack:
            move = fifo_stack.pop(0)
            last_move = move
            move_value = move.value
            if at_date:
                move_value = move._get_value(at_date=at_date)
            if qty_on_first_move:
                valued_qty = move._get_valued_qty()
                in_qty = qty_on_first_move
                in_value = move_value * in_qty / valued_qty
                qty_on_first_move = 0
            else:
                in_qty = move._get_valued_qty()
                in_value = move_value
            if in_qty > quantity:
                in_value = in_value * quantity / in_qty
                in_qty = quantity
            fifo_cost += in_value
            quantity -= in_qty
        # When we required more quantity than available we extrapolate with the last known price
        if quantity > 0:
            if last_move and last_move.quantity:
                fifo_cost += quantity * (last_move.value / last_move.quantity)
            else:
                fifo_cost += quantity * self.standard_price
        return fifo_cost