def _apply_updates(self, payment_data):
        """Override of `payment` to update the transaction based on the payment data."""
        if self.provider_code != 'nuvei':
            return super()._apply_updates(payment_data)

        if not payment_data:
            self._set_canceled(state_message=_("The customer left the payment page."))
            return

        # Update the provider reference.
        self.provider_reference = payment_data.get('TransactionID')

        # Update the payment method.
        payment_option = payment_data.get('payment_method', '')
        payment_method = self.env['payment.method']._get_from_code(
            payment_option, mapping=const.PAYMENT_METHODS_MAPPING
        )
        self.payment_method_id = payment_method or self.payment_method_id

        # Update the payment state.
        status = payment_data.get('Status') or payment_data.get('ppp_status')
        if not status:
            self._set_error(_("Received data with missing payment state."))
            return
        status = status.lower()
        if status in const.PAYMENT_STATUS_MAPPING['pending']:
            self._set_pending()
        elif status in const.PAYMENT_STATUS_MAPPING['done']:
            self._set_done()
        elif status in const.PAYMENT_STATUS_MAPPING['error']:
            failure_reason = payment_data.get('Reason') or payment_data.get('message')
            self._set_error(_(
                "An error occurred during the processing of your payment (%(reason)s). Please try"
                " again.", reason=failure_reason,
            ))
        else:  # Classify unsupported payment states as the `error` tx state.
            status_description = payment_data.get('Reason')
            _logger.info(
                "Received data with invalid payment status (%(status)s) and reason '%(reason)s' "
                "for transaction %(ref)s.",
                {'status': status, 'reason': status_description, 'ref': self.reference},
            )
            self._set_error(_(
                "Received invalid transaction status %(status)s and reason '%(reason)s'.",
                status=status, reason=status_description
            ))