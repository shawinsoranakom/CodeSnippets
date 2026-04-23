def create_backend_pos_order(self, data):
        pos_config = data.get('pos_config', self.pos_config)
        order_data = data.get('order_data', {})
        line_product_ids = [line_data['product_id'] for line_data in data.get('line_data', [])]
        product_by_id = {p.id: p for p in self.env['product.product'].browse(line_product_ids)}
        refund = False

        if not pos_config.current_session_id:
            pos_config.open_ui()

        order = self.env['pos.order'].create({
            'amount_total': 0,
            'amount_paid': 0,
            'amount_tax': 0,
            'amount_return': 0,
            'date_order': fields.Datetime.to_string(fields.Datetime.now()),
            'company_id': self.env.company.id,
            'session_id': pos_config.current_session_id.id,
            'lines': [
                Command.create({
                    'price_unit': product_by_id[line_data['product_id']].lst_price,
                    'price_subtotal': product_by_id[line_data['product_id']].lst_price,
                    'tax_ids': [(6, 0, product_by_id[line_data['product_id']].taxes_id.ids)],
                    'price_subtotal_incl': 0,
                    **line_data,
                }) for line_data in data.get('line_data', [])
            ],
            **order_data,
        })

        # Re-trigger prices computation
        order.lines._onchange_amount_line_all()
        order._compute_prices()

        if data.get('payment_data'):
            payment_context = {"active_ids": order.ids, "active_id": order.id}
            for payment in data['payment_data']:
                make_payment = {'payment_method_id': payment['payment_method_id']}
                if payment.get('amount'):
                    make_payment['amount'] = payment['amount']
                order_payment = self.env['pos.make.payment'].with_context(**payment_context).create(make_payment)
                order_payment.with_context(**payment_context).check()

        if data.get('refund_data'):
            refund_action = order.refund()
            refund = self.env['pos.order'].browse(refund_action['res_id'])
            payment_context = {"active_ids": refund.ids, "active_id": refund.id}

            if data.get('order_data') and data['order_data'].get('to_invoice', False):
                refund.to_invoice = True

            for refund_data in data['refund_data']:
                make_refund = {'payment_method_id': refund_data['payment_method_id']}
                if refund_data.get('amount'):
                    make_refund['amount'] = refund_data['amount']
                refund_payment = self.env['pos.make.payment'].with_context(**payment_context).create(make_refund)
                refund_payment.with_context(**payment_context).check()

        return order, refund