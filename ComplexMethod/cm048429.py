def create(self, vals_list):
        for vals in vals_list:
            if vals.get('move_id'):
                vals['company_id'] = self.env['stock.move'].browse(vals['move_id']).company_id.id
            elif vals.get('picking_id'):
                vals['company_id'] = self.env['stock.picking'].browse(vals['picking_id']).company_id.id
            if vals.get('move_id') and 'picked' not in vals:
                vals['picked'] = self.env['stock.move'].browse(vals['move_id']).picked
            if vals.get('quant_id'):
                vals.update(self._copy_quant_info(vals))

        mls = super().create(vals_list)

        created_moves = set()

        def create_move(move_line):
            new_move = self.env['stock.move'].create(move_line._prepare_stock_move_vals())
            move_line.move_id = new_move.id
            created_moves.add(new_move.id)

        # If the move line is directly create on the picking view.
        # If this picking is already done we should generate an
        # associated done move.
        for move_line in mls:
            if move_line.move_id or not move_line.picking_id:
                continue
            if move_line.picking_id.state != 'done':
                moves = move_line._get_linkable_moves()
                if moves:
                    vals = {
                        'move_id': moves[0].id,
                        'picking_id': moves[0].picking_id.id,
                    }
                    if moves[0].picked:
                        vals['picked'] = True
                    move_line.write(vals)
                else:
                    create_move(move_line)
            else:
                create_move(move_line)

        move_to_recompute_state = set()
        for move_line in mls:
            if move_line.state == 'done':
                continue
            location = move_line.location_id
            product = move_line.product_id
            move = move_line.move_id
            if move:
                reservation = not move._should_bypass_reservation()
            else:
                reservation = product.is_storable and not location.should_bypass_reservation()
            if move_line.quantity_product_uom and reservation:
                self.env.context.get('reserved_quant', self.env['stock.quant'])._update_reserved_quantity(
                    product, location, move_line.quantity_product_uom, lot_id=move_line.lot_id, package_id=move_line.package_id, owner_id=move_line.owner_id)

                if move:
                    move_to_recompute_state.add(move.id)
        self.env['stock.move'].browse(move_to_recompute_state)._recompute_state()
        self.env['stock.move'].browse(created_moves)._post_process_created_moves()

        for ml in mls:
            if ml.state == 'done':
                if ml.product_id.is_storable:
                    Quant = self.env['stock.quant']
                    quantity = ml.product_uom_id._compute_quantity(ml.quantity, ml.move_id.product_id.uom_id, rounding_method='HALF-UP')
                    available_qty, in_date = Quant._update_available_quantity(ml.product_id, ml.location_id, -quantity, lot_id=ml.lot_id, package_id=ml.package_id, owner_id=ml.owner_id)
                    if available_qty < 0 and ml.lot_id:
                        # see if we can compensate the negative quants with some untracked quants
                        untracked_qty = Quant._get_available_quantity(ml.product_id, ml.location_id, lot_id=False, package_id=ml.package_id, owner_id=ml.owner_id, strict=True)
                        if untracked_qty:
                            taken_from_untracked_qty = min(untracked_qty, abs(quantity))
                            Quant._update_available_quantity(ml.product_id, ml.location_id, -taken_from_untracked_qty, lot_id=False, package_id=ml.package_id, owner_id=ml.owner_id)
                            Quant._update_available_quantity(ml.product_id, ml.location_id, taken_from_untracked_qty, lot_id=ml.lot_id, package_id=ml.package_id, owner_id=ml.owner_id)
                    Quant._update_available_quantity(ml.product_id, ml.location_dest_id, quantity, lot_id=ml.lot_id, package_id=ml.result_package_id, owner_id=ml.owner_id, in_date=in_date)
                next_moves = ml.move_id.move_dest_ids.filtered(lambda move: move.state not in ('done', 'cancel'))
                next_moves._do_unreserve()
                next_moves._action_assign()
        move_done = mls.filtered(lambda m: m.state == "done").move_id
        if move_done:
            move_done._check_quantity()
        return mls