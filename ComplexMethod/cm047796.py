def write(self, vals):
        if 'product_id' in vals and self.state != 'draft':
            vals.pop('product_id')
        if 'move_byproduct_ids' in vals and 'move_finished_ids' not in vals:
            vals['move_finished_ids'] = vals.get('move_finished_ids', []) + vals['move_byproduct_ids']
            del vals['move_byproduct_ids']
        if 'bom_id' in vals and 'move_byproduct_ids' in vals and 'move_finished_ids' in vals:
            # If byproducts are given, they take precedence over move_finished for byproduts definition
            bom = self.env['mrp.bom'].browse(vals.get('bom_id'))
            bom_product = bom.product_id or bom.product_tmpl_id.product_variant_id
            joined_move_ids = vals.get('move_byproduct_ids', [])
            for move_finished in vals.get('move_finished_ids', []):
                # Remove CREATE lines from finished_ids as they do not reflect the form current state (nor the byproduct vals)
                if move_finished[0] == Command.CREATE and move_finished[2].get('product_id') != bom_product.id:
                    continue
                joined_move_ids.append(move_finished)
            vals['move_finished_ids'] = joined_move_ids
            del vals['move_byproduct_ids']
        if 'workorder_ids' in self:
            production_to_replan = self.filtered(lambda p: p.is_planned)
        for move_str in ('move_raw_ids', 'move_finished_ids'):
            if move_str not in vals or self.state in ['cancel', 'done']:
                continue
            # When adding a move raw/finished, it should have the source location's `warehouse_id`.
            # Before, it was handle by an onchange, now it's forced if not already in vals.
            warehouse_id = self.location_src_id.warehouse_id.id
            if vals.get('location_src_id'):
                location_source = self.env['stock.location'].browse(vals.get('location_src_id'))
                warehouse_id = location_source.warehouse_id.id
            for move_vals in vals[move_str]:
                if move_vals[0] != Command.CREATE:
                    continue
                _command, _id, field_values = move_vals
                if not field_values.get('warehouse_id'):
                    field_values['warehouse_id'] = warehouse_id

        moves_to_reassign = self.env['stock.move']
        if vals.get('picking_type_id'):
            picking_type = self.env['stock.picking.type'].browse(vals.get('picking_type_id'))
            for production in self:
                if production.state in ('cancel', 'done'):
                    continue
                if picking_type != production.picking_type_id:
                    production.name = picking_type.sequence_id.next_by_id()
                    moves_to_reassign |= production.move_raw_ids

        res = super(MrpProduction, self).write(vals)

        for production in self:
            if 'date_start' in vals and not self.env.context.get('force_date', False):
                if production.state in ['done', 'cancel']:
                    raise UserError(_('You cannot move a manufacturing order once it is cancelled or done.'))
                if production.is_planned:
                    production.button_unplan()
            if vals.get('date_start'):
                production.move_raw_ids.write({'date': production.date_start, 'date_deadline': production.date_start})
            if vals.get('date_finished'):
                production.move_finished_ids.write({'date': production.date_finished})
            if any(field in ['move_raw_ids', 'move_finished_ids', 'workorder_ids'] for field in vals) and production.state != 'draft':
                production.with_context(no_procurement=True)._autoconfirm_production()
                if production in production_to_replan:
                    production._plan_workorders()
            if production.state == 'done' and 'qty_producing' in vals:
                finished_move = production.move_finished_ids.filtered(
                    lambda move: move.product_id == production.product_id and move.state == 'done')
                finished_move.quantity = vals.get('qty_producing')
            if self._has_workorders() and not production.workorder_ids.operation_id and vals.get('date_start') and not vals.get('date_finished'):
                new_date_start = fields.Datetime.to_datetime(vals.get('date_start'))
                if not production.date_finished or new_date_start >= production.date_finished:
                    production.date_finished = new_date_start + datetime.timedelta(hours=1)
        if moves_to_reassign:
            moves_to_reassign._do_unreserve()
            moves_to_reassign = moves_to_reassign.filtered(
                lambda move: move.state in ('confirmed', 'partially_available')
                and (move._should_bypass_reservation()
                    or move.picking_type_id.reservation_method == 'at_confirm'
                    or (move.reservation_date and move.reservation_date <= fields.Date.today())))
            moves_to_reassign._action_assign()
        return res