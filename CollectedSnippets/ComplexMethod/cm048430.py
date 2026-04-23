def write(self, vals):
        if 'product_id' in vals and any(vals.get('state', ml.state) != 'draft' and vals['product_id'] != ml.product_id.id for ml in self):
            raise UserError(_("Changing the product is only allowed in 'Draft' state."))

        if ('lot_id' in vals or 'quant_id' in vals) and len(self.product_id) > 1:
            raise UserError(_("Changing the Lot/Serial number for move lines with different products is not allowed."))

        moves_to_recompute_state = self.env['stock.move']
        packages_to_check = self.env['stock.package']
        if 'result_package_id' in vals:
            # Either changed the result package or removed it
            packages_to_check = self.env['stock.package'].browse(self.result_package_id._get_all_package_dest_ids())
        triggers = [
            ('location_id', 'stock.location'),
            ('location_dest_id', 'stock.location'),
            ('lot_id', 'stock.lot'),
            ('package_id', 'stock.package'),
            ('result_package_id', 'stock.package'),
            ('owner_id', 'res.partner'),
            ('product_uom_id', 'uom.uom')
        ]
        if vals.get('quant_id'):
            vals.update(self._copy_quant_info(vals))
        updates = {}
        for key, model in triggers:
            if self.env.context.get('skip_uom_conversion'):
                continue
            if key in vals:
                updates[key] = vals[key] if isinstance(vals[key], models.BaseModel) else self.env[model].browse(vals[key])

        # When we try to write on a reserved move line any fields from `triggers`, result_package_id excepted,
        # or directly reserved_uom_qty` (the actual reserved quantity), we need to make sure the associated
        # quants are correctly updated in order to not make them out of sync (i.e. the sum of the
        # move lines `reserved_uom_qty` should always be equal to the sum of `reserved_quantity` on
        # the quants). If the new charateristics are not available on the quants, we chose to
        # reserve the maximum possible.
        if (updates and {'result_package_id'}.difference(updates.keys())) or 'quantity' in vals:
            for ml in self:
                if not ml.product_id.is_storable or ml.state == 'done':
                    continue
                if 'quantity' in vals or 'product_uom_id' in vals:
                    new_ml_uom = updates.get('product_uom_id', ml.product_uom_id)
                    new_reserved_qty = new_ml_uom._compute_quantity(
                        vals.get('quantity', ml.quantity), ml.product_id.uom_id, rounding_method='HALF-UP')
                    # Make sure `reserved_uom_qty` is not negative.
                    if ml.product_id.uom_id.compare(new_reserved_qty, 0) < 0:
                        raise UserError(_('Reserving a negative quantity is not allowed.'))
                else:
                    new_reserved_qty = ml.quantity_product_uom

                # Unreserve the old charateristics of the move line.
                if not ml.product_uom_id.is_zero(ml.quantity_product_uom):
                    ml._synchronize_quant(-ml.quantity_product_uom, ml.location_id, action="reserved")

                # Reserve the maximum available of the new charateristics of the move line.
                if not ml.move_id._should_bypass_reservation(updates.get('location_id', ml.location_id)):
                    ml._synchronize_quant(
                        new_reserved_qty, updates.get('location_id', ml.location_id), action="reserved",
                        lot=updates.get('lot_id', ml.lot_id), package=updates.get('package_id', ml.package_id),
                        owner=updates.get('owner_id', ml.owner_id))

                if ('quantity' in vals and vals['quantity'] != ml.quantity) or 'product_uom_id' in vals:
                    moves_to_recompute_state |= ml.move_id

        # When editing a done move line, the reserved availability of a potential chained move is impacted. Take care of running again `_action_assign` on the concerned moves.
        mls = self.env['stock.move.line']
        if updates or 'quantity' in vals:
            next_moves = self.env['stock.move']
            mls = self.filtered(lambda ml: ml.move_id.state == 'done' and ml.product_id.is_storable)
            if not updates:  # we can skip those where quantity is already good up to UoM rounding
                mls = mls.filtered(lambda ml: not ml.product_uom_id.is_zero(ml.quantity - vals['quantity']))
            for ml in mls:
                # undo the original move line
                in_date = ml._synchronize_quant(-ml.quantity_product_uom, ml.location_dest_id, package=ml.result_package_id)[1]
                ml._synchronize_quant(ml.quantity_product_uom, ml.location_id, in_date=in_date)

                # Unreserve and reserve following move in order to have the real reserved quantity on move_line.
                next_moves |= ml.move_id.move_dest_ids.filtered(lambda move: move.state not in ('done', 'cancel'))

                # Log a note
                if ml.picking_id:
                    ml._log_message(ml.picking_id, ml, 'stock.track_move_template', vals)
            move_done = mls.move_id
            if move_done:
                move_done._check_quantity()

        # update the date when it seems like (additional) quantities are "done" and the date hasn't been manually updated
        if 'date' not in vals and ('product_uom_id' in vals or 'quantity' in vals or vals.get('picked', False)):
            updated_ml_ids = set()
            for ml in self:
                if ml.state in ['draft', 'cancel', 'done']:
                    continue
                if vals.get('picked', False) and not ml.picked:
                    updated_ml_ids.add(ml.id)
                    continue
                if ('quantity' in vals or 'product_uom_id' in vals) and ml.picked:
                    new_qty = updates.get('product_uom_id', ml.product_uom_id)._compute_quantity(vals.get('quantity', ml.quantity), ml.product_id.uom_id, rounding_method='HALF-UP')
                    old_qty = ml.product_uom_id._compute_quantity(ml.quantity, ml.product_id.uom_id, rounding_method='HALF-UP')
                    if ml.product_uom_id.compare(old_qty, new_qty) < 0:
                        updated_ml_ids.add(ml.id)
            self.env['stock.move.line'].browse(updated_ml_ids).date = fields.Datetime.now()

        res = super(StockMoveLine, self).write(vals)

        for ml in mls:
            available_qty, dummy = ml._synchronize_quant(-ml.quantity_product_uom, ml.location_id)
            ml._synchronize_quant(ml.quantity_product_uom, ml.location_dest_id, package=ml.result_package_id)
            if available_qty < 0:
                ml._free_reservation(
                    ml.product_id, ml.location_id,
                    abs(available_qty), lot_id=ml.lot_id, package_id=ml.package_id,
                    owner_id=ml.owner_id)

        if packages_to_check:
            # Clear the dest from packages if not linked to any active picking
            packages_to_check.filtered(lambda p: p.package_dest_id and not p.picking_ids).package_dest_id = False
        if updates or 'quantity' in vals:
            # Updated fields could imply that entire packs are no longer entire.
            if mls_to_update := self._get_lines_not_entire_pack():
                mls_to_update.write({'is_entire_pack': False})

        # As stock_account values according to a move's `product_uom_qty`, we consider that any
        # done stock move should have its `quantity_done` equals to its `product_uom_qty`, and
        # this is what move's `action_done` will do. So, we replicate the behavior here.
        if updates or 'quantity' in vals:
            next_moves._do_unreserve()
            next_moves._action_assign()

        if moves_to_recompute_state:
            moves_to_recompute_state._recompute_state()

        return res