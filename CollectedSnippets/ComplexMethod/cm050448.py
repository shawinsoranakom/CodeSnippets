def check(self):
        """Check the order:
        if the order is not paid: continue payment,
        if the order is paid print ticket.
        """
        self.ensure_one()

        order = self.env['pos.order'].browse(self.env.context.get('active_id', False))
        if self.payment_method_id.split_transactions and not order.partner_id:
            raise UserError(_(
                "Customer is required for %s payment method.",
                self.payment_method_id.name
            ))

        currency = order.currency_id

        init_data = self.read()[0]
        payment_method = self.env['pos.payment.method'].browse(init_data['payment_method_id'][0])
        if not float_is_zero(init_data['amount'], precision_rounding=currency.rounding):
            order.add_payment({
                'pos_order_id': order.id,
                'amount': order._get_rounded_amount(init_data['amount'], payment_method.is_cash_count or not self.config_id.only_round_cash_method),
                'name': init_data['payment_name'],
                'payment_method_id': init_data['payment_method_id'][0],
            })

        if order.state == 'draft' and order._is_pos_order_paid():
            order._process_saved_order(False)
            if order.state in {'paid', 'done'}:
                order._send_order()
                order.config_id.notify_synchronisation(order.config_id.current_session_id.id, 0)
            return {'type': 'ir.actions.act_window_close'}

        return self.launch_payment()