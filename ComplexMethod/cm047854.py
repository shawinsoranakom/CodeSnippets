def _run_procurement(self, old_qties=False):
        procurements = []
        old_qties = old_qties or {}
        to_assign = self.env['stock.move']
        self._adjust_procure_method()
        for move in self:
            if move.product_uom.compare(move.product_uom_qty - old_qties.get(move.id, 0), 0) < 0\
                    and move.procure_method == 'make_to_order'\
                    and move.move_orig_ids and all(m.state == 'done' for m in move.move_orig_ids):
                continue
            if move.product_uom.compare(move.product_uom_qty, 0) > 0:
                if move._should_bypass_reservation() \
                        or move.picking_type_id.reservation_method == 'at_confirm' \
                        or (move.reservation_date and move.reservation_date <= fields.Date.today()):
                    to_assign |= move

            if move.procure_method == 'make_to_order' or move.rule_id.procure_method == 'mts_else_mto':
                procurement_qty = move.product_uom_qty - old_qties.get(move.id, 0)
                if move.move_orig_ids:
                    possible_reduceable_qty = -sum(move.move_orig_ids.filtered(lambda m: m.state not in ('done', 'cancel') and m.product_uom_qty).mapped('product_uom_qty'))
                    procurement_qty = max(procurement_qty, possible_reduceable_qty)
                values = move._prepare_procurement_values()
                procurements.append(self.env['stock.rule'].Procurement(
                    move.product_id, procurement_qty, move.product_uom,
                    move.location_id, move.reference, move.origin, move.company_id, values))

        to_assign._action_assign()
        if procurements:
            self.env['stock.rule'].run(procurements)