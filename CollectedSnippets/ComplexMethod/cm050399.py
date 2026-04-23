def _compute_qty_at_date(self):
        """ Compute the quantity forecasted of product at delivery date. There are
        two cases:
         1. The quotation has a commitment_date, we take it as delivery date
         2. The quotation hasn't commitment_date, we compute the estimated delivery
            date based on lead time"""
        treated = self.browse()
        all_move_ids = {
            move.id
            for line in self
            if line.state == 'sale'
            for move in line.move_ids | self.env['stock.move'].browse(line.move_ids._rollup_move_origs())
            if move.product_id == line.product_id
        }
        all_moves = self.env['stock.move'].browse(all_move_ids)
        forecast_expected_date_per_move = dict(all_moves.mapped(lambda m: (m.id, m.forecast_expected_date)))
        # If the state is already in sale the picking is created and a simple forecasted quantity isn't enough
        # Then used the forecasted data of the related stock.move
        for line in self.filtered(lambda l: l.state == 'sale'):
            if not line.display_qty_widget:
                continue
            moves = line.move_ids | self.env['stock.move'].browse(line.move_ids._rollup_move_origs())
            moves = moves.filtered(
                lambda m: m.product_id == line.product_id and m.state not in ('cancel', 'done'))
            line.forecast_expected_date = max(
                (
                    forecast_expected_date_per_move[move.id]
                    for move in moves
                    if forecast_expected_date_per_move[move.id]
                ),
                default=False,
            )
            line.qty_available_today = 0
            line.free_qty_today = 0
            for move in moves:
                line.qty_available_today += move.product_uom._compute_quantity(move.quantity, line.product_uom_id)
                line.free_qty_today += move.product_id.uom_id._compute_quantity(move.forecast_availability, line.product_uom_id)
            line.scheduled_date = line.order_id.commitment_date or line._expected_date()
            line.virtual_available_at_date = False
            treated |= line

        qty_processed_per_product = defaultdict(lambda: 0)
        grouped_lines = defaultdict(lambda: self.env['sale.order.line'])
        # We first loop over the SO lines to group them by warehouse and schedule
        # date in order to batch the read of the quantities computed field.
        for line in self.filtered(lambda l: l.state in ('draft', 'sent')):
            if not (line.product_id and line.display_qty_widget):
                continue
            grouped_lines[(line.warehouse_id.id, line.order_id.commitment_date or line._expected_date())] |= line

        for (warehouse, scheduled_date), lines in grouped_lines.items():
            product_qties = lines._read_qties(scheduled_date, warehouse)
            qties_per_product = {
                product['id']: (product['qty_available'], product['free_qty'], product['virtual_available'])
                for product in product_qties
            }
            for line in lines:
                line.scheduled_date = scheduled_date
                qty_available_today, free_qty_today, virtual_available_at_date = qties_per_product[line.product_id.id]
                line.qty_available_today = qty_available_today - qty_processed_per_product[line.product_id.id]
                line.free_qty_today = free_qty_today - qty_processed_per_product[line.product_id.id]
                line.virtual_available_at_date = virtual_available_at_date - qty_processed_per_product[line.product_id.id]
                line.forecast_expected_date = False
                product_qty = line.product_uom_qty
                if line.product_uom_id and line.product_id.uom_id and line.product_uom_id != line.product_id.uom_id:
                    line.qty_available_today = line.product_id.uom_id._compute_quantity(line.qty_available_today, line.product_uom_id)
                    line.free_qty_today = line.product_id.uom_id._compute_quantity(line.free_qty_today, line.product_uom_id)
                    line.virtual_available_at_date = line.product_id.uom_id._compute_quantity(line.virtual_available_at_date, line.product_uom_id)
                    product_qty = line.product_uom_id._compute_quantity(product_qty, line.product_id.uom_id)
                qty_processed_per_product[line.product_id.id] += product_qty
            treated |= lines
        remaining = (self - treated)
        remaining.virtual_available_at_date = False
        remaining.scheduled_date = False
        remaining.forecast_expected_date = False
        remaining.free_qty_today = False
        remaining.qty_available_today = False