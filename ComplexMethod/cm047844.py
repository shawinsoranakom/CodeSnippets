def action_unbuild(self):
        self.ensure_one()
        self._check_company()
        # remove the default_* keys that were only needed in the unbuild wizard
        self = self.with_env(self.env(context=clean_context(self.env.context)))  # noqa: PLW0642
        if self.product_id.tracking != 'none' and not self.lot_id.id:
            raise UserError(_('You should provide a lot number for the final product.'))

        if self.mo_id and self.mo_id.state != 'done':
            raise UserError(_('You cannot unbuild a undone manufacturing order.'))

        consume_moves = self._generate_consume_moves()
        consume_moves._action_confirm()
        produce_moves = self._generate_produce_moves()
        produce_moves._action_confirm()
        produce_moves.quantity = 0

        # Collect component lots already restored by previous unbuilds on the same MO
        previously_unbuilt_lots = (self.mo_id.unbuild_ids - self).produce_line_ids.filtered(lambda ml: ml.product_id != self.product_id and ml.product_id.tracking == 'serial').lot_ids

        finished_moves = consume_moves.filtered(lambda m: m.product_id == self.product_id)
        consume_moves -= finished_moves
        error_message = _(
            "Please specify a manufacturing order.\n"
            "It will allow us to retrieve the lots/serial numbers of the correct components and/or byproducts."
        )

        if any(produce_move.has_tracking != 'none' and not self.mo_id for produce_move in produce_moves):
            raise UserError(error_message)

        if any(consume_move.has_tracking != 'none' and not self.mo_id for consume_move in consume_moves):
            raise UserError(error_message)

        for finished_move in finished_moves:
            if float_compare(finished_move.product_uom_qty, finished_move.quantity, precision_rounding=finished_move.product_uom.rounding) > 0:
                finished_move_line_vals = self._prepare_finished_move_line_vals(finished_move)
                self.env['stock.move.line'].create(finished_move_line_vals)

        # TODO: Will fail if user do more than one unbuild with lot on the same MO. Need to check what other unbuild has aready took
        qty_already_used = defaultdict(float)
        for move in produce_moves | consume_moves:
            if float_compare(move.product_uom_qty, move.quantity, precision_rounding=move.product_uom.rounding) < 1:
                continue
            original_move = move in produce_moves and self.mo_id.move_raw_ids or self.mo_id.move_finished_ids
            original_move = original_move.filtered(lambda m: m.product_id == move.product_id)
            if not original_move:
                move.quantity = move.product_uom.round(move.product_uom_qty)
                continue
            needed_quantity = move.product_uom_qty
            moves_lines = original_move.mapped('move_line_ids')
            if move in produce_moves and self.lot_id:
                moves_lines = moves_lines.filtered(
                    lambda ml: self.lot_id in ml.produce_line_ids.lot_id and ml.lot_id not in previously_unbuilt_lots
                )
            for move_line in moves_lines:
                # Iterate over all move_lines until we unbuilded the correct quantity.
                taken_quantity = min(needed_quantity, move_line.quantity - qty_already_used[move_line])
                taken_quantity = move.product_uom.round(taken_quantity)
                if taken_quantity:
                    move_line_vals = self._prepare_move_line_vals(move, move_line, taken_quantity)
                    if move_line.owner_id:
                        move_line_vals['owner_id'] = move_line.owner_id.id
                    unbuild_move_line = self.env["stock.move.line"].create(move_line_vals)
                    needed_quantity -= taken_quantity
                    qty_already_used[move_line] += taken_quantity
                    unbuild_move_line._apply_putaway_strategy()
            if move in produce_moves and float_compare(needed_quantity, 0, precision_rounding=move.product_uom.rounding) > 0:
                move.quantity += needed_quantity

        (finished_moves | consume_moves | produce_moves).picked = True
        finished_moves._action_done()
        consume_moves._action_done()
        produce_moves._action_done()
        produced_move_line_ids = produce_moves.mapped('move_line_ids').filtered(lambda ml: ml.quantity > 0)
        consume_moves.mapped('move_line_ids').write({'produce_line_ids': [(6, 0, produced_move_line_ids.ids)]})
        if self.mo_id:
            unbuild_msg = _("%(qty)s %(measure)s unbuilt in %(order)s",
                qty=self.product_qty,
                measure=self.product_uom_id.name,
                order=self._get_html_link(),
            )
            self.mo_id.message_post(
                body=unbuild_msg,
                subtype_xmlid='mail.mt_note',
            )
        return self.write({'state': 'done'})