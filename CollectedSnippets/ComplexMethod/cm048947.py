def _process_order(self, order, existing_order):
        res = super()._process_order(order, existing_order)
        refunded_line_ids = [line[2].get('refunded_orderline_id') for line in order.get('lines') if line[0] in [0, 1] and line[2].get('refunded_orderline_id')]
        refunded_orderlines = self.env['pos.order.line'].browse(refunded_line_ids)
        event_to_cancel = []

        for refunded_orderline in refunded_orderlines:
            if refunded_orderline.event_registration_ids:
                refund_qty = abs(sum(refunded_orderline.refund_orderline_ids.mapped('qty')))
                already_cancelled_qty = len(refunded_orderline.event_registration_ids.filtered(lambda r: r.state == 'cancel'))
                to_cancel_qty = refund_qty - already_cancelled_qty
                if to_cancel_qty > 0:
                    event_to_cancel += refunded_orderline.event_registration_ids.filtered(lambda registration: registration.state != 'cancel').ids[:int(to_cancel_qty)]

        if event_to_cancel:
            self.env['event.registration'].browse(event_to_cancel).write({'state': 'cancel'})

        return res