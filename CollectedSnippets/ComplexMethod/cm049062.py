def _post_process(self):
        """ Override of `payment` to add Sales-specific logic to the post-processing.

        In particular, for pending transactions, we send the quotation by email; for authorized
        transactions, we confirm the quotation; for confirmed transactions, we automatically confirm
        the quotation and generate invoices.
        """
        for pending_tx in self.filtered(lambda tx: tx.state == 'pending'):
            super(PaymentTransaction, pending_tx)._post_process()
            sales_orders = pending_tx.sale_order_ids.filtered(
                lambda so: so.state in ['draft', 'sent']
            )
            sales_orders.filtered(
                lambda so: so.state == 'draft'
            ).with_context(tracking_disable=True).action_quotation_sent()

            if pending_tx.provider_id.code == 'custom':
                for order in pending_tx.sale_order_ids:
                    order.reference = pending_tx._compute_sale_order_reference(order)

            if pending_tx.operation == 'validation':
                continue
            # Send the payment status email.
            # The transactions are manually cached while in a sudoed environment to prevent an
            # AccessError: In some circumstances, sending the mail would generate the report assets
            # during the rendering of the mail body, causing a cursor commit, a flush, and forcing
            # the re-computation of the pending computed fields of the `mail.compose.message`,
            # including part of the template. Since that template reads the order's transactions and
            # the re-computation of the field is not done with the same environment, reading fields
            # that were not already available in the cache could trigger an AccessError (e.g., if
            # the payment was initiated by a public user).
            sales_orders.mapped('transaction_ids')
            sales_orders._send_payment_succeeded_for_order_mail()

        for authorized_tx in self.filtered(lambda tx: tx.state == 'authorized'):
            super(PaymentTransaction, authorized_tx)._post_process()
            confirmed_orders = authorized_tx._check_amount_and_confirm_order()
            if authorized_tx.operation == 'validation':
                continue
            if remaining_orders := (authorized_tx.sale_order_ids - confirmed_orders):
                remaining_orders._send_payment_succeeded_for_order_mail()

        super(PaymentTransaction, self.filtered(
            lambda tx: tx.state not in ['pending', 'authorized', 'done'])
        )._post_process()

        for done_tx in self.filtered(lambda tx: tx.state == 'done'):
            if done_tx.operation != 'validation':
                confirmed_orders = done_tx._check_amount_and_confirm_order()
                (done_tx.sale_order_ids - confirmed_orders)._send_payment_succeeded_for_order_mail()

            auto_invoice = str2bool(
                self.env['ir.config_parameter'].sudo().get_param('sale.automatic_invoice')
            )
            if auto_invoice:
                # Invoice the sales orders of confirmed transactions instead of only confirmed
                # orders to create the invoice even if only a partial payment was made.
                done_tx._invoice_sale_orders()
            super(PaymentTransaction, done_tx)._post_process()  # Post the invoices.
            if auto_invoice and not self.env.context.get('skip_sale_auto_invoice_send'):
                if (
                    str2bool(self.env['ir.config_parameter'].sudo().get_param('sale.async_emails'))
                    and (send_invoice_cron := self.env.ref('sale.send_invoice_cron', raise_if_not_found=False))
                ):
                    send_invoice_cron._trigger()
                else:
                    self._send_invoice()