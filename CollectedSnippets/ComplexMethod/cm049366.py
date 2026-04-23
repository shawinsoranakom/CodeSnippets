def _apply_updates(self, payment_data):
        """Override of `payment` to update the transaction based on the payment data."""
        if self.provider_code != 'demo':
            return super()._apply_updates(payment_data)

        # Update the provider reference.
        self.provider_reference = f'demo-{self.reference}'

        # Create the token.
        if self.tokenize:
            # The reasons why we immediately tokenize the transaction instead of in `payment` are:
            # - To save the simulated state and payment details on the token while we have them.
            # - To allow customers to create tokens whose transactions will always end up in the
            #   said simulated state.
            self._tokenize(payment_data)

        # Update the payment state.
        state = payment_data['simulated_state']
        if state == 'pending':
            self._set_pending()
        elif state == 'done':
            if self.capture_manually and not payment_data.get('manual_capture'):
                self._set_authorized()
            else:
                self._set_done()
                # Immediately post-process the transaction if it is a refund, as the post-processing
                # will not be triggered by a customer browsing the transaction from the portal.
                if self.operation == 'refund':
                    self.env.ref('payment.cron_post_process_payment_tx')._trigger()
        elif state == 'cancel':
            self._set_canceled()
        else:  # Simulate an error state.
            self._set_error(_("You selected the following demo payment status: %s", state))