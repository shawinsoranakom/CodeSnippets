def _compute_delivery_status(self):
        for order in self:
            if not order.picking_ids or all(p.state == 'cancel' for p in order.picking_ids):
                order.delivery_status = False
            elif all(p.state in ['done', 'cancel'] for p in order.picking_ids):
                order.delivery_status = 'full'
            elif any(p.state == 'done' for p in order.picking_ids) and any(
                    l.qty_delivered for l in order.order_line):
                order.delivery_status = 'partial'
            elif any(p.state == 'done' for p in order.picking_ids):
                order.delivery_status = 'started'
            else:
                order.delivery_status = 'pending'