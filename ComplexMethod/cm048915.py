def _apply_updates(self, payment_data):
        """Override of `payment` to update the transaction based on the payment data."""
        if self.provider_code != 'authorize':
            return super()._apply_updates(payment_data)

        response_content = payment_data.get('response')

        # Update the provider reference.
        self.provider_reference = response_content.get('x_trans_id')

        # Update the payment method.
        payment_method_code = response_content.get('payment_method_code', '').lower()
        payment_method = self.env['payment.method']._get_from_code(
            payment_method_code, mapping=const.PAYMENT_METHODS_MAPPING
        )
        self.payment_method_id = payment_method or self.payment_method_id

        # Update the payment state.
        status_code = response_content.get('x_response_code', '3')
        if status_code == '1':  # Approved
            status_type = response_content.get('x_type').lower()
            if status_type in ('auth_capture', 'prior_auth_capture'):
                self._set_done()
            elif status_type == 'auth_only':
                self._set_authorized()
                if self.operation == 'validation':
                    self._void()  # In last step because it processes the response.
            elif status_type == 'void':
                # - If operation is refund, we are in a child transaction created in _refund(),
                #   and having the void status means the payment was voided instead of refunded,
                #   because the payment was not settled yet. In this case, we should mark the
                #   refund transaction as done, since we are in the child transaction.
                # - For validation transactions, they are authorized and then voided:
                #   If the void went through, the validation transaction is confirmed.
                if self.operation in ['validation', 'refund']:
                    self._set_done()
                else:
                    self._set_canceled(extra_allowed_states=('done',))
            elif status_type == 'refund' and self.operation == 'refund':
                self._set_done()
                # Immediately post-process the transaction as the post-processing will not be
                # triggered by a customer browsing the transaction from the portal.
                self.env.ref('payment.cron_post_process_payment_tx')._trigger()
        elif status_code == '2':  # Declined
            self._set_canceled(state_message=response_content.get('x_response_reason_text'))
        elif status_code == '4':  # Held for Review
            self._set_pending()
        else:  # Error / Unknown code
            error_code = response_content.get('x_response_reason_text')
            _logger.info(
                "Received data with invalid status (%(status)s) and error code (%(err)s) for "
                "transaction %(ref)s.",
                {
                    'status': status_code,
                    'err': error_code,
                    'ref': self.reference,
                },
            )
            self._set_error(_(
                "Received data with status code \"%(status)s\" and error code \"%(error)s\".",
                status=status_code, error=error_code
            ))