def _check_sn_uniqueness(self):
        """ Alert the user if the serial number as already been consumed/produced """
        self.ensure_one()
        if self.product_tracking == 'serial' and self.lot_producing_ids:
            lots_to_check = self.lot_producing_ids.filtered(lambda l: l.id not in self.move_raw_ids.lot_ids.ids)
            if lots_to_check and self._are_finished_serials_already_produced(lots_to_check):
                raise UserError(_('Serial number(s) for product %(product_name)s already produced', product_name=self.product_id.name))

        for move in self.move_finished_ids:
            if move.has_tracking != 'serial' or move.product_id == self.product_id:
                continue
            for move_line in move.move_line_ids:
                if move_line.product_uom_id.is_zero(move_line.quantity):
                    continue
                if self._are_finished_serials_already_produced(move_line.lot_id, excluded_sml=move_line):
                    raise UserError(_('The serial number %(number)s used for byproduct %(product_name)s has already been produced',
                                      number=move_line.lot_id.name, product_name=move_line.product_id.name))

        consumed_sn_ids = []
        sn_error_msg = {}
        for move in self.move_raw_ids:
            if move.has_tracking != 'serial' or not move.picked:
                continue
            for move_line in move.move_line_ids:
                if not move_line.picked or move_line.product_uom_id.is_zero(move_line.quantity) or not move_line.lot_id:
                    continue
                sml_sn = move_line.lot_id
                message = _('The serial number %(number)s used for component %(component)s has already been consumed',
                    number=sml_sn.name,
                    component=move_line.product_id.name)
                consumed_sn_ids.append(sml_sn.id)
                sn_error_msg[sml_sn.id] = message
                co_prod_move_lines = self.move_raw_ids.move_line_ids
                duplicates = co_prod_move_lines.filtered(lambda ml: ml.quantity and ml.lot_id == sml_sn) - move_line
                if duplicates:
                    raise UserError(message)

        if not consumed_sn_ids:
            return

        consumed_sml_groups = self.env['stock.move.line']._read_group([
            ('lot_id', 'in', consumed_sn_ids),
            ('quantity', '=', 1),
            ('state', '=', 'done'),
            ('location_dest_id.usage', '=', 'production'),
            ('production_id', '!=', False),
        ], ['lot_id'], ['quantity:sum'])
        consumed_qties = {lot.id: qty for lot, qty in consumed_sml_groups}
        problematic_sn_ids = list(consumed_qties.keys())
        if not problematic_sn_ids:
            return

        cancelled_sml_groups = self.env['stock.move.line']._read_group([    # SML that cancels the SN consumption
            ('lot_id', 'in', problematic_sn_ids),
            ('quantity', '=', 1),
            ('state', '=', 'done'),
            ('location_id.usage', '=', 'production'),
            '|',
                ('move_id.production_id', '=', False),
                '&',
                    ('move_id.production_id', '!=', False),
                    ('move_id.production_id.product_id', '=', self.product_id.id),
        ], ['lot_id'], ['quantity:sum'])
        cancelled_qties = defaultdict(float, {lot.id: qty for lot, qty in cancelled_sml_groups})

        for sn_id in problematic_sn_ids:
            consumed_qty = consumed_qties[sn_id]
            cancelled_qty = cancelled_qties[sn_id]
            if consumed_qty - cancelled_qty > 0:
                raise UserError(sn_error_msg[sn_id])