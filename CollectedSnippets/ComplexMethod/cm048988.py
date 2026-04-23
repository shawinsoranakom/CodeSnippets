def _apply_updates(self, payment_data):
        """Override of payment to update the transaction based on the payment data."""
        if self.provider_code != 'iyzico':
            return super()._apply_updates(payment_data)

        # Update the provider reference.
        self.provider_reference = payment_data.get('paymentId')

        # Update the payment method.
        if bool(payment_data.get('cardType')):
            payment_method_code = payment_data.get('cardAssociation', '')
            payment_method = self.env['payment.method']._get_from_code(
                payment_method_code.lower(), mapping=const.PAYMENT_METHODS_MAPPING
            )
        elif bool(payment_data.get('bankName')):
            payment_method = self.env.ref('payment.payment_method_bank_transfer')
        else:
            payment_method = self.env.ref('payment.payment_method_unknown')
        self.payment_method_id = payment_method or self.payment_method_id

        # Update the payment state.
        status = payment_data.get('paymentStatus')
        if status in const.PAYMENT_STATUS_MAPPING['pending']:
            self._set_pending()
        elif status in const.PAYMENT_STATUS_MAPPING['done']:
            self._set_done()
        elif status in const.PAYMENT_STATUS_MAPPING['error']:
            self._set_error(self.env._(
                "An error occurred during processing of your payment (code %(code)s:"
                " %(explanation)s). Please try again.",
                code=status, explanation=payment_data.get('errorMessage'),
            ))
        else:
            _logger.warning(
                "Received data with invalid payment status (%s) for transaction with reference %s",
                status, self.reference
            )
            self._set_error(self.env._("Unknown status code: %s", status))