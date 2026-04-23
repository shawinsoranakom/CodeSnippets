def button_validate(self):
        self._check_can_validate()
        cost_without_adjusment_lines = self.filtered(lambda c: not c.valuation_adjustment_lines)
        if cost_without_adjusment_lines:
            cost_without_adjusment_lines.compute_landed_cost()
        if not self._check_sum():
            raise UserError(_('Cost and adjustments lines do not match. You should maybe recompute the landed costs.'))

        for cost in self:
            cost = cost.with_company(cost.company_id)
            move = self.env['account.move']
            move_vals = {
                'journal_id': cost.account_journal_id.id,
                'date': cost.date,
                'ref': cost.name,
                'line_ids': [],
                'move_type': 'entry',
            }
            for line in cost.valuation_adjustment_lines.filtered(lambda line: line.move_id):
                product = line.move_id.product_id
                # Products with manual inventory valuation are ignored because they do not need to create journal entries.
                if product.valuation != "real_time":
                    continue
                # `remaining_qty` is negative if the move is out and delivered proudcts that were not
                # in stock.

                remaining_qty = line.move_id.remaining_qty
                move_vals['line_ids'] += line._create_accounting_entries(remaining_qty)

            # batch standard price computation avoid recompute quantity_svl at each iteration

            # products = self.env['product.product'].browse(p.id for p in cost_to_add_byproduct.keys()).with_company(cost.company_id)
            # for product in products:  # iterate on recordset to prefetch efficiently quantity_svl
            #     if not product.uom_id.is_zero(product.quantity_svl):
            #         product.sudo().with_context(disable_auto_svl=True).standard_price += cost_to_add_byproduct[product] / product.quantity_svl
            #     if product.lot_valuated:
            #         for lot, value in cost_to_add_bylot[product].items():
            #             if product.uom_id.is_zero(lot.quantity_svl):
            #                 continue
            #             lot.sudo().with_context(disable_auto_svl=True).standard_price += value / lot.quantity_svl

            # We will only create the accounting entry when there are defined lines (the lines will be those linked to products of real_time valuation category).
            cost_vals = {'state': 'done'}
            if move_vals.get("line_ids"):
                move = move.create(move_vals)
                cost_vals.update({'account_move_id': move.id})
            cost.write(cost_vals)
            if cost.account_move_id:
                move._post()
            cost.valuation_adjustment_lines.move_id._set_value()
        return True