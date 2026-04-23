def write(self, vals):
        if vals.get('order_line') and self.state == 'purchase':
            for order in self:
                pre_order_line_qty = {order_line: order_line.product_qty for order_line in order.mapped('order_line')}
        res = super(PurchaseOrder, self).write(vals)
        if vals.get('order_line') and self.state == 'purchase':
            for order in self:
                to_log = {}
                for order_line in order.order_line:
                    if pre_order_line_qty.get(order_line) and order_line.product_uom_id.compare(pre_order_line_qty[order_line], order_line.product_qty) > 0:
                        to_log[order_line] = (order_line.product_qty, pre_order_line_qty[order_line])
                if to_log:
                    order._log_decrease_ordered_quantity(to_log)
        return res