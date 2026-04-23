def _launch_stock_rule_from_pos_order_lines(self):

        procurements = []
        for line in self:
            line = line.with_company(line.company_id)
            if line.product_id.type != 'consu':
                continue

            reference_ids = line.order_id.stock_reference_ids
            if not reference_ids:
                reference_ids = self.env['stock.reference'].create(line._prepare_reference_vals())
                line.order_id.stock_reference_ids = [Command.set(reference_ids.ids)]

            values = line._prepare_procurement_values()
            product_qty = line.qty

            procurement_uom = line.product_id.uom_id
            procurements.append(self.env['stock.rule'].Procurement(
                line.product_id, product_qty, procurement_uom,
                line.order_id.partner_id.property_stock_customer,
                line.name, line.order_id.name, line.order_id.company_id, values))
        if procurements:
            self.env['stock.rule'].run(procurements)

        # This next block is currently needed only because the scheduler trigger is done by picking confirmation rather than stock.move confirmation
        orders = self.mapped('order_id')
        for order in orders:
            pickings_to_confirm = order.picking_ids
            if pickings_to_confirm:
                # Trigger the Scheduler for Pickings
                tracked_lines = order.lines.filtered(lambda l: l.product_id.tracking != 'none')
                lines_by_tracked_product = groupby(sorted(tracked_lines, key=lambda l: l.product_id.id), key=lambda l: l.product_id.id)
                pickings_to_confirm.action_confirm()
                for product_id, lines in lines_by_tracked_product:
                    lines = self.env['pos.order.line'].concat(*lines)
                    moves = pickings_to_confirm.move_ids.filtered(lambda m: m.product_id.id == product_id)
                    moves.move_line_ids.unlink()
                    moves._add_mls_related_to_order(lines, are_qties_done=False)
                    moves._recompute_state()
        return True