def _apply_updates(self, payment_data):
        """Override of `payment` to update the transaction based on the payment data."""
        if self.provider_code != 'stripe':
            return super()._apply_updates(payment_data)

        # Update the payment method.
        payment_method = payment_data.get('payment_method')
        if isinstance(payment_method, dict):  # capture/void/refund requests receive a string.
            payment_method_type = payment_method.get('type')
            if self.payment_method_id.code == payment_method_type == 'card':
                payment_method_type = payment_data['payment_method']['card']['brand']
            payment_method = self.env['payment.method']._get_from_code(
                payment_method_type, mapping=const.PAYMENT_METHODS_MAPPING
            )
            self.payment_method_id = payment_method or self.payment_method_id

        # Update the provider reference and the payment state.
        if self.operation == 'validation':
            self.provider_reference = payment_data['setup_intent']['id']
            status = payment_data['setup_intent']['status']
        elif self.operation == 'refund':
            self.provider_reference = payment_data['refund']['id']
            status = payment_data['refund']['status']
        else:  # 'online_direct', 'online_token', 'offline'
            self.provider_reference = payment_data['payment_intent']['id']
            status = payment_data['payment_intent']['status']
        if not status:
            self._set_error(_("Received data with missing intent status."))
        elif status in const.STATUS_MAPPING['draft']:
            pass
        elif status in const.STATUS_MAPPING['pending']:
            self._set_pending()
        elif status in const.STATUS_MAPPING['authorized']:
            self._set_authorized()
        elif status in const.STATUS_MAPPING['done']:
            self._set_done()

            # Immediately post-process the transaction if it is a refund, as the post-processing
            # will not be triggered by a customer browsing the transaction from the portal.
            if self.operation == 'refund':
                self.env.ref('payment.cron_post_process_payment_tx')._trigger()
        elif status in const.STATUS_MAPPING['cancel']:
            self._set_canceled()
        elif status in const.STATUS_MAPPING['error']:
            if self.operation != 'refund':
                last_payment_error = payment_data.get('payment_intent', {}).get(
                    'last_payment_error'
                )
                if last_payment_error:
                    message = last_payment_error.get('message', {})
                else:
                    message = _("The customer left the payment page.")
                self._set_error(message)
            else:
                self._set_error(_(
                    "The refund did not go through. Please log into your Stripe Dashboard to get "
                    "more information on that matter, and address any accounting discrepancies."
                ), extra_allowed_states=('done',))
        else:  # Classify unknown intent statuses as `error` tx state
            _logger.warning(
                "Received invalid payment status (%s) for transaction %s.",
                status, self.reference
            )
            self._set_error(_("Received data with invalid intent status: %s.", status))