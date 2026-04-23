def _apply_updates(self, payment_data):
        """Override of `payment` to update the transaction based on the payment data."""
        if self.provider_code != 'flutterwave':
            return super()._apply_updates(payment_data)

        # Update the provider reference.
        self.provider_reference = payment_data['id']

        # Update payment method.
        payment_method_type = payment_data.get('payment_type', '')
        if payment_method_type == 'card':
            payment_method_type = payment_data.get('card', {}).get('type').lower()
        payment_method = self.env['payment.method']._get_from_code(
            payment_method_type, mapping=const.PAYMENT_METHODS_MAPPING
        )
        self.payment_method_id = payment_method or self.payment_method_id

        # Update the payment state.
        payment_status = payment_data['status'].lower()
        if payment_status in const.PAYMENT_STATUS_MAPPING['pending']:
            auth_url = payment_data.get('meta', {}).get('authorization', {}).get('redirect')
            if auth_url:
                # will be set back to the actual value after moving away from pending
                self.provider_reference = auth_url
            self._set_pending()
        elif payment_status in const.PAYMENT_STATUS_MAPPING['done']:
            self._set_done()
        elif payment_status in const.PAYMENT_STATUS_MAPPING['cancel']:
            self._set_canceled()
        elif payment_status in const.PAYMENT_STATUS_MAPPING['error']:
            self._set_error(_(
                "An error occurred during the processing of your payment (status %s). Please try "
                "again.", payment_status
            ))
        else:
            _logger.warning(
                "Received data with invalid payment status (%s) for transaction %s.",
                payment_status, self.reference
            )
            self._set_error(_("Unknown payment status: %s", payment_status))