def write(self, vals):
        if 'product_uom_qty' in vals:
            old_product_uom_qty = {line.id: line.product_uom_qty for line in self}
            res = super().write(vals)
            for line in self:
                if line.state in ('sale', 'done') and line.product_id:
                    if line.product_uom_id.compare(old_product_uom_qty[line.id], 0) <= 0 and line.product_uom_id.compare(line.product_uom_qty, 0) > 0:
                        self._create_repair_order()
                    if line.product_uom_id.compare(old_product_uom_qty[line.id], 0) > 0 and line.product_uom_id.compare(line.product_uom_qty, 0) <= 0:
                        self._cancel_repair_order()
            return res
        return super().write(vals)