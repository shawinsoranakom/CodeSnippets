def _apply_updates(self, payment_data):
        """Override of `payment` to update the transaction based on the payment data."""
        if self.provider_code != 'xendit':
            return super()._apply_updates(payment_data)

        # Update the provider reference.
        self.provider_reference = payment_data.get('id')

        # Update payment method.
        # If it's one of FPX Methods, assign the payment method as FPX automatically
        payment_method_code = payment_data.get('payment_method', '')
        if payment_method_code in const.FPX_METHODS:
            payment_method_code = 'fpx'

        payment_method = self.env['payment.method']._get_from_code(
            payment_method_code, mapping=const.PAYMENT_METHODS_MAPPING
        )
        self.payment_method_id = payment_method or self.payment_method_id

        # Update the payment state.
        payment_status = payment_data.get('status')
        if payment_status in const.PAYMENT_STATUS_MAPPING['pending']:
            self._set_pending()
        elif payment_status in const.PAYMENT_STATUS_MAPPING['done']:
            self._set_done()
        elif payment_status in const.PAYMENT_STATUS_MAPPING['cancel']:
            self._set_canceled()
        elif payment_status in const.PAYMENT_STATUS_MAPPING['error']:
            failure_reason = payment_data.get('failure_reason')
            self._set_error(_(
                "An error occurred during the processing of your payment (%s). Please try again.",
                failure_reason,
            ))