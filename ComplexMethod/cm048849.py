def _compute_receipt_status(self):
        for order in self:
            if not order.picking_ids or all(p.state == 'cancel' for p in order.picking_ids):
                order.receipt_status = False
            elif all(p.state in ['done', 'cancel'] for p in order.picking_ids):
                order.receipt_status = 'full'
            elif any(p.state == 'done' for p in order.picking_ids):
                order.receipt_status = 'partial'
            else:
                order.receipt_status = 'pending'