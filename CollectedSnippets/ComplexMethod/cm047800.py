def _set_qty_producing(self, pick_manual_consumption_moves=True):
        if self.product_id.tracking == 'serial':
            qty_producing_uom = self.product_uom_id._compute_quantity(self.qty_producing, self.product_id.uom_id, rounding_method='HALF-UP')
            qty_production_uom = self.product_uom_id._compute_quantity(self.product_qty, self.product_id.uom_id, rounding_method='HALF-UP')
            # allow changing a non-zero value to a 0 to not block mass produce feature
            if qty_producing_uom != qty_production_uom and not (qty_producing_uom == 0 and self._origin.qty_producing != self.qty_producing):
                self.qty_producing = self.product_id.uom_id._compute_quantity(len(self.lot_producing_ids), self.product_uom_id, rounding_method='HALF-UP')

        # waiting for a preproduction move before assignement
        is_waiting = self.warehouse_id.manufacture_steps != 'mrp_one_step' and self.picking_ids.filtered(lambda p: p.picking_type_id == self.warehouse_id.pbm_type_id and p.state not in ('done', 'cancel'))

        for move in (
            self.move_raw_ids.filtered(lambda m: not is_waiting or m.product_id.tracking == 'none')
            | self.move_finished_ids.filtered(lambda m: m.product_id != self.product_id or m.product_id.tracking == 'serial')
        ):
            is_byproduct = move in self.move_byproduct_ids
            # Never update already produced by-product moves.
            if move.picked and (is_byproduct or move.manual_consumption):
                continue

            # sudo needed for portal users
            if move.sudo()._should_bypass_set_qty_producing():
                continue

            new_qty = move.product_uom.round((self.qty_producing - self.qty_produced) * move.unit_factor)
            move._set_quantity_done(new_qty)
            if (not move.manual_consumption or pick_manual_consumption_moves) \
                    and move.quantity \
                    and not is_byproduct \
                    and (move.raw_material_production_id or move.product_id.tracking != 'serial'):
                move.picked = True