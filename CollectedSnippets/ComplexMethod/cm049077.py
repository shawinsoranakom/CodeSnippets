def _compute_value(self):
        self.fetch(['company_id', 'location_id', 'owner_id', 'product_id', 'quantity', 'lot_id'])
        self.value = 0
        for quant in self:
            if not quant.location_id or not quant.product_id or\
                    not quant.location_id._should_be_valued() or\
                    quant._should_exclude_for_valuation() or\
                    quant.product_id.uom_id.is_zero(quant.quantity):
                continue
            if quant.product_id.lot_valuated:
                quantity = quant.lot_id.with_company(quant.company_id).product_qty
                value = quant.lot_id.with_company(quant.company_id).total_value
            else:
                quantity = quant.product_id.with_company(quant.company_id)._with_valuation_context().qty_available
                value = quant.product_id.with_company(quant.company_id).total_value
            if quant.product_id.uom_id.is_zero(quantity):
                continue
            quant.value = quant.quantity * value / quantity