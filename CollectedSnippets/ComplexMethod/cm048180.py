def _apply_updates(self, payment_data):
        """ Override of `payment' to process the transaction based on Worldline data.

        Note: self.ensure_one()

        :param dict payment_data: The payment data sent by the provider.
        :return: None
        """
        if self.provider_code != 'worldline':
            return super()._apply_updates(payment_data)

        # In case of failed payment, paymentResult could be given as a separate key
        payment_result = payment_data.get('paymentResult', payment_data)
        payment_data = payment_result.get('payment', {})

        # Update the provider reference.
        self.provider_reference = payment_data.get('id', '').rsplit('_', 1)[0]

        # Update the payment method.
        payment_method_data = self._worldline_extract_payment_method_data(payment_data)
        payment_method_code = payment_method_data.get('paymentProductId', '')
        payment_method = self.env['payment.method']._get_from_code(
            payment_method_code, mapping=const.PAYMENT_METHODS_MAPPING
        )
        self.payment_method_id = payment_method or self.payment_method_id

        # Update the payment state.
        status = payment_data.get('status')
        has_token_data = 'token' in payment_method_data
        if not status:
            self._set_error(_("Received data with missing payment state."))
        elif status in const.PAYMENT_STATUS_MAPPING['pending']:
            if status == 'AUTHORIZATION_REQUESTED' and self.operation in ('online_token', 'offline'):
                self._set_error(status)
            elif self.operation == 'validation' \
                 and status in {'PENDING_CAPTURE', 'CAPTURE_REQUESTED'} \
                 and has_token_data:
                    self._set_done()
            else:
                self._set_pending()
        elif status in const.PAYMENT_STATUS_MAPPING['done']:
            self._set_done()
        else:
            error_code = None
            if errors := payment_data.get('statusOutput', {}).get('errors'):
                error_code = errors[0].get('errorCode')
            if status in const.PAYMENT_STATUS_MAPPING['cancel']:
                self._set_canceled(_(
                    "Transaction cancelled with error code %(error_code)s.",
                    error_code=error_code,
                ))
            elif status in const.PAYMENT_STATUS_MAPPING['declined']:
                self._set_error(_(
                    "Transaction declined with error code %(error_code)s.",
                    error_code=error_code,
                ))
            else:  # Classify unsupported payment status as the `error` tx state.
                _logger.info(
                    "Received data with invalid payment status (%(status)s) for transaction with "
                    "reference %(ref)s.",
                    {'status': status, 'ref': self.reference},
                )
                self._set_error(_(
                    "Received invalid transaction status %(status)s with error code "
                    "%(error_code)s.",
                    status=status,
                    error_code=error_code,
                ))