def _run_fifo_get_stack(self, lot=None, at_date=None, location=None):
        # TODO: return a list of tuple (move, valued_qty) instead
        external_location = location and location.is_valued_external
        fifo_stack = []
        fifo_stack_size = 0
        if location:
            self = self.with_context(location=location.ids)  # noqa: PLW0642
        if lot:
            fifo_stack_size = lot.product_qty
        else:
            fifo_stack_size = self._with_valuation_context().with_context(to_date=at_date).qty_available
        if self.env.context.get('fifo_qty_already_processed'):
            # When validating multiple moves at the same time, the qty_available won't be up to date yet
            fifo_stack_size -= self.env.context['fifo_qty_already_processed']
        if self.uom_id.compare(fifo_stack_size, 0) <= 0:
            return fifo_stack, 0

        moves_domain = Domain([
            ('product_id', '=', self.id),
            ('company_id', '=', self.env.company.id)
        ])
        if lot:
            moves_domain &= Domain([('move_line_ids.lot_id', 'in', lot.id)])
        if at_date:
            moves_domain &= Domain([('date', '<=', at_date)])
        if location:
            moves_domain &= Domain([('location_dest_id', '=', location.id)])
        if external_location:
            moves_domain &= Domain([('is_out', '=', True)])
        else:
            moves_domain &= Domain([('is_in', '=', True)])

        # Arbitrary limit as we can't guess how many moves correspond to the qty_available, but avoid fetching all moves at the same time.
        initial_limit = 100
        moves_in = self.env['stock.move'].search(moves_domain, order='date desc, id desc', limit=initial_limit)

        remaining_qty_on_first_stack_move = 0
        current_offset = 0
        # Go to the bottom of the stack
        while self.uom_id.compare(fifo_stack_size, 0) > 0 and moves_in:
            move = moves_in[0]
            moves_in = moves_in[1:]
            in_qty = move._get_valued_qty()
            fifo_stack.append(move)
            remaining_qty_on_first_stack_move = min(in_qty, fifo_stack_size)
            fifo_stack_size -= in_qty
            if self.uom_id.compare(fifo_stack_size, 0) > 0 and not moves_in:
                # We need to fetch more moves
                current_offset += 1
                moves_in = self.env['stock.move'].search(moves_domain, order='date desc, id desc', offset=current_offset * initial_limit, limit=initial_limit)
        fifo_stack.reverse()
        return fifo_stack, remaining_qty_on_first_stack_move