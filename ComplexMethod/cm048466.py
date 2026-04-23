def write(self, vals):
        # Handle the write on the initial demand by updating the reserved quantity and logging
        # messages according to the state of the stock.move records.
        receipt_moves_to_reassign = self.env['stock.move']
        move_to_recompute_state = self.env['stock.move']
        move_to_check_location = self.env['stock.move']
        if 'quantity' in vals:
            if any(move.state == 'cancel' for move in self):
                raise UserError(_('You cannot change a cancelled stock move, create a new line instead.'))
        if 'product_uom' in vals and any(move.state == 'done' for move in self) and not self.env.context.get('skip_uom_conversion'):
            raise UserError(_('You cannot change the UoM for a stock move that has been set to \'Done\'.'))
        if 'product_uom_qty' in vals:
            for move in self.filtered(lambda m: m.state not in ('done', 'draft') and m.picking_id):
                if move.product_uom.compare(vals['product_uom_qty'], move.product_uom_qty):
                    self.env['stock.move.line']._log_message(move.picking_id, move, 'stock.track_move_template', vals)
            if self.env.context.get('do_not_unreserve') is None:
                move_to_unreserve = self.filtered(
                    lambda m: m.state not in ['draft', 'done', 'cancel'] and m.product_uom.compare(m.quantity, vals.get('product_uom_qty')) == 1
                )
                move_to_unreserve._do_unreserve()
                (self - move_to_unreserve).filtered(lambda m: m.state == 'assigned').write({'state': 'partially_available'})
                # When editing the initial demand, directly run again action assign on receipt moves.
                receipt_moves_to_reassign |= move_to_unreserve.filtered(lambda m: m.location_id.usage == 'supplier')
                receipt_moves_to_reassign |= (self - move_to_unreserve).filtered(
                    lambda m:
                        m.location_id.usage == 'supplier' and
                        m.state in ('partially_available', 'assigned')
                )
                move_to_recompute_state |= self - move_to_unreserve - receipt_moves_to_reassign
        if 'date_deadline' in vals:
            self._set_date_deadline(vals.get('date_deadline'))
        if 'move_orig_ids' in vals:
            move_to_recompute_state |= self.filtered(lambda m: m.state not in ['draft', 'cancel', 'done'])
        if 'location_id' in vals:
            move_to_check_location = self.filtered(lambda m: m.location_id.id != vals.get('location_id'))
        if 'product_id' in vals or 'location_id' in vals or 'location_dest_id' in vals:
            self._update_orderpoints()
        res = super().write(vals)
        moves_done = self.filtered(lambda m: m.state == 'done')
        if 'date' in vals and moves_done:
            moves_done.move_line_ids.date = vals['date']
        if move_to_recompute_state:
            move_to_recompute_state._recompute_state()
        if move_to_check_location:
            for ml in move_to_check_location.move_line_ids:
                parent_path = [int(loc_id) for loc_id in ml.location_id.parent_path.split('/')[:-1]]
                if move_to_check_location.location_id.id not in parent_path:
                    receipt_moves_to_reassign |= move_to_check_location
                    move_to_check_location.procure_method = 'make_to_stock'
                    move_to_check_location.move_orig_ids = [Command.clear()]
                    ml.unlink()
        if 'location_id' in vals or 'location_dest_id' in vals:
            wh_by_moves = defaultdict(self.env['stock.move'].browse)
            for move in self:
                move_warehouse = move.location_id.warehouse_id or move.location_dest_id.warehouse_id
                if move_warehouse == move.warehouse_id:
                    continue
                wh_by_moves[move_warehouse] |= move
            for warehouse, moves in wh_by_moves.items():
                moves.warehouse_id = warehouse.id
        if receipt_moves_to_reassign:
            receipt_moves_to_reassign._action_assign()
        if ('product_id' in vals or 'state' in vals or 'date' in vals or 'product_uom_qty' in vals or
                'location_id' in vals or 'location_dest_id' in vals):
            self._update_orderpoints()
        if 'picking_id' in vals:
            self._set_references()
        return res