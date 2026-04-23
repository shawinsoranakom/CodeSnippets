def _compute_value(self):
        """Compute totals of multiple svl related values"""
        company_id = self.env.company
        self.company_currency_id = company_id.currency_id
        at_date = fields.Datetime.to_datetime(self.env.context.get('to_date'))
        for lot in self:
            if not lot.lot_valuated:
                lot.total_value = 0.0
                lot.avg_cost = 0.0
                continue
            valuated_product = lot.product_id.with_context(at_date=at_date, lot_id=lot.id)
            qty_valued = lot.product_qty
            qty_available = lot.with_context(warehouse_id=False).product_qty
            if valuated_product.uom_id.is_zero(qty_valued):
                lot.total_value = 0
                lot.avg_cost = 0.0
            elif valuated_product.cost_method == 'standard' or valuated_product.uom_id.is_zero(qty_available):
                lot.total_value = lot.standard_price * qty_valued
                lot.avg_cost = lot.standard_price
            elif valuated_product.cost_method == 'average':
                avco_result = valuated_product.with_context(warehouse_id=False)._run_avco(at_date=at_date, lot=lot.with_context(warehouse_id=False))
                lot.total_value = avco_result[1] * qty_valued / qty_available
                lot.avg_cost = avco_result[0]
            else:
                fifo_value = valuated_product.with_context(warehouse_id=False)._run_fifo(qty_available, at_date=at_date, lot=lot.with_context(warehouse_id=False))
                lot.total_value = fifo_value * qty_valued / qty_available
                lot.avg_cost = fifo_value / qty_available if qty_available else 0.0