def _apply_updates(self, payment_data):
        """Override of `payment` to update the transaction based on the payment data."""
        if self.provider_code != 'buckaroo':
            return super()._apply_updates(payment_data)

        # Update the provider reference.
        transaction_keys = payment_data.get('brq_transactions')
        if not transaction_keys:
            self._set_error(_("Received data with missing transaction keys"))
            return
        # BRQ_TRANSACTIONS can hold multiple, comma-separated, tx keys. In practice, it holds only
        # one reference. So we split for semantic correctness and keep the first transaction key.
        self.provider_reference = transaction_keys.split(',')[0]

        # Update the payment method.
        payment_method_code = payment_data.get('brq_payment_method')
        payment_method = self.env['payment.method']._get_from_code(
            payment_method_code, mapping=const.PAYMENT_METHODS_MAPPING
        )
        self.payment_method_id = payment_method or self.payment_method_id

        # Update the payment state.
        status_code = int(payment_data.get('brq_statuscode') or 0)
        if status_code in const.STATUS_CODES_MAPPING['pending']:
            self._set_pending()
        elif status_code in const.STATUS_CODES_MAPPING['done']:
            self._set_done()
        elif status_code in const.STATUS_CODES_MAPPING['cancel']:
            self._set_canceled()
        elif status_code in const.STATUS_CODES_MAPPING['refused']:
            self._set_error(_("Your payment was refused (code %s). Please try again.", status_code))
        elif status_code in const.STATUS_CODES_MAPPING['error']:
            self._set_error(_(
                "An error occurred during processing of your payment (code %s). Please try again.",
                status_code,
            ))
        else:
            _logger.warning(
                "Received data with invalid payment status (%s) for transaction %s.",
                status_code, self.reference
            )
            self._set_error(_("Unknown status code: %s.", status_code))