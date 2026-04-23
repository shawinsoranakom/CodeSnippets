def write(self, vals):
        increased_lines = None
        decreased_lines = None
        increased_values = {}
        decreased_values = {}
        if 'product_uom_qty' in vals:
            precision = self.env['decimal.precision'].precision_get('Product Unit')
            increased_lines = self.sudo().filtered(lambda r: r.product_id.with_company(r._purchase_service_get_company()).service_to_purchase and r.purchase_line_count and float_compare(r.product_uom_qty, vals['product_uom_qty'], precision_digits=precision) == -1)
            decreased_lines = self.sudo().filtered(lambda r: r.product_id.with_company(r._purchase_service_get_company()).service_to_purchase and r.purchase_line_count and float_compare(r.product_uom_qty, vals['product_uom_qty'], precision_digits=precision) == 1)
            increased_values = {line.id: line.product_uom_qty for line in increased_lines}
            decreased_values = {line.id: line.product_uom_qty for line in decreased_lines}

        result = super().write(vals)

        if increased_lines:
            increased_lines._purchase_increase_ordered_qty(vals['product_uom_qty'], increased_values)
        if decreased_lines:
            decreased_lines._purchase_decrease_ordered_qty(vals['product_uom_qty'], decreased_values)
        return result