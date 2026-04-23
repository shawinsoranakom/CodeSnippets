def _post_inventory(self, cancel_backorder=False):
        moves_to_do, moves_not_to_do, moves_to_cancel = set(), set(), set()
        for move in self.move_raw_ids:
            if move.state == 'done':
                moves_not_to_do.add(move.id)
            elif not move.picked:
                moves_to_cancel.add(move.id)
            elif move.state != 'cancel':
                moves_to_do.add(move.id)

        self.with_context(skip_mo_check=True).env['stock.move'].browse(moves_to_do)._action_done(cancel_backorder=cancel_backorder)
        self.with_context(skip_mo_check=True).env['stock.move'].browse(moves_to_cancel)._action_cancel()
        moves_to_do = self.move_raw_ids.filtered(lambda x: x.state == 'done') - self.env['stock.move'].browse(moves_not_to_do)
        # Create a dict to avoid calling filtered inside for loops.
        moves_to_do_by_order = defaultdict(lambda: self.env['stock.move'], [
            (key, self.env['stock.move'].concat(*values))
            for key, values in tools_groupby(moves_to_do, key=lambda m: m.raw_material_production_id.id)
        ])
        for order in self:
            finish_moves = order.move_finished_ids.filtered(lambda m: m.product_id == order.product_id and m.state not in ('done', 'cancel'))
            # the finish move can already be completed by the workorder.
            for move in finish_moves:
                if move.has_tracking != 'none' and not move.lot_ids:
                    move.lot_ids = order.lot_producing_ids.ids
                move.quantity = order.product_uom_id.round(order.qty_producing - order.qty_produced, rounding_method='HALF-UP')
                extra_vals = order._prepare_finished_extra_vals()
                if extra_vals:
                    move.move_line_ids.write(extra_vals)
            # workorder duration need to be set to calculate the price of the product
            for workorder in order.workorder_ids:
                if workorder.state not in ('done', 'cancel'):
                    workorder.duration_expected = workorder._get_duration_expected()
                if workorder.state == 'cancel':
                    workorder.duration = 0.0
                elif workorder.duration == 0.0:
                    workorder.duration = workorder.duration_expected
                    workorder.duration_unit = round(workorder.duration / max(workorder.qty_produced, 1), 2)
            order._cal_price(moves_to_do_by_order[order.id])
        moves_to_finish = self.move_finished_ids.filtered(lambda x: x.state not in ('done', 'cancel'))
        moves_to_finish.picked = True
        moves_to_finish = moves_to_finish._action_done(cancel_backorder=cancel_backorder)
        for order in self:
            consume_move_lines = moves_to_do_by_order[order.id].mapped('move_line_ids')
            order.move_finished_ids.move_line_ids.consume_line_ids = [(6, 0, consume_move_lines.ids)]
        return True