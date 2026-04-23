def _apply_updates(self, payment_data):
        """Override of `payment` to update the transaction based on the payment data."""
        if self.provider_code != 'paypal':
            return super()._apply_updates(payment_data)

        if not payment_data:
            self._set_canceled(state_message=_("The customer left the payment page."))
            return

        # Update the provider reference.
        txn_id = payment_data.get('id')
        txn_type = payment_data.get('txn_type')
        if not all((txn_id, txn_type)):
            self._set_error(_(
                "Missing value for txn_id (%(txn_id)s) or txn_type (%(txn_type)s).",
                txn_id=txn_id, txn_type=txn_type
            ))
            return
        self.provider_reference = txn_id
        self.paypal_type = txn_type

        # Force PayPal as the payment method if it exists.
        self.payment_method_id = self.env['payment.method'].search(
            [('code', '=', 'paypal')], limit=1
        ) or self.payment_method_id

        # Update the payment state.
        payment_status = payment_data.get('status')

        if payment_status in PAYMENT_STATUS_MAPPING['pending']:
            self._set_pending(state_message=payment_data.get('pending_reason'))
        elif payment_status in PAYMENT_STATUS_MAPPING['done']:
            self._set_done()
        elif payment_status in PAYMENT_STATUS_MAPPING['cancel']:
            self._set_canceled()
        else:
            _logger.info(
                "Received data with invalid payment status (%s) for transaction %s.",
                payment_status, self.reference
            )
            self._set_error(_("Received data with invalid payment status: %s", payment_status))