def _apply_updates(self, payment_data):
        """Override of payment to update the transaction based on the payment data."""
        if self.provider_code != 'adyen':
            return super()._apply_updates(payment_data)

        # Extract or assume the event code. If none is provided, the feedback data originate from a
        # direct payment request whose feedback data share the same payload as an 'AUTHORISATION'
        # webhook notification.
        event_code = payment_data.get('eventCode', 'AUTHORISATION')

        # Update the provider reference. If the event code is 'CAPTURE' or 'CANCELLATION', we
        # discard the pspReference as it is different from the original pspReference of the tx.
        if 'pspReference' in payment_data and event_code in ['AUTHORISATION', 'REFUND']:
            self.provider_reference = payment_data.get('pspReference')

        # Update the payment method.
        payment_method_data = payment_data.get('paymentMethod', '')
        if isinstance(payment_method_data, dict):  # Not from webhook: the data contain the PM code.
            payment_method_type = payment_method_data['type']
            if payment_method_type == 'scheme':  # card
                payment_method_code = payment_method_data['brand']
            else:
                payment_method_code = payment_method_type
        else:  # Sent from the webhook: the PM code is directly received as a string.
            payment_method_code = payment_method_data

        payment_method = self.env['payment.method']._get_from_code(
            payment_method_code, mapping=const.PAYMENT_METHODS_MAPPING
        )
        self.payment_method_id = payment_method or self.payment_method_id

        # Update the payment state.
        payment_state = payment_data.get('resultCode')
        refusal_reason = payment_data.get('refusalReason') or payment_data.get('reason')
        if not payment_state:
            self._set_error(_("Received data with missing payment state."))
        elif payment_state in const.RESULT_CODES_MAPPING['pending']:
            self._set_pending()
        elif payment_state in const.RESULT_CODES_MAPPING['done']:
            if not self.provider_id.capture_manually:
                self._set_done()
            else:  # The payment was configured for manual capture.
                # Differentiate the state based on the event code.
                if event_code == 'AUTHORISATION':
                    self._set_authorized()
                else:  # 'CAPTURE'
                    self._set_done()

            # Immediately post-process the transaction if it is a refund, as the post-processing
            # will not be triggered by a customer browsing the transaction from the portal.
            if self.operation == 'refund':
                self.env.ref('payment.cron_post_process_payment_tx')._trigger()
        elif payment_state in const.RESULT_CODES_MAPPING['cancel']:
            self._set_canceled()
        elif payment_state in const.RESULT_CODES_MAPPING['error']:
            if event_code in ['AUTHORISATION', 'REFUND']:
                _logger.warning(
                    "The transaction %s underwent an error. reason: %s.",
                    self.reference, refusal_reason,
                )
                self._set_error(
                    _("An error occurred during the processing of your payment. Please try again.")
                )
            elif event_code == 'CANCELLATION':
                _logger.warning(
                    "The void of the transaction %s failed. reason: %s.",
                    self.reference, refusal_reason,
                )
                if self.source_transaction_id:  # child tx => The event can't be retried.
                    self._set_error(_("The void of the transaction %s failed.", self.reference))
                else:  # source tx with failed void stays in its state, could be voided again
                    self._log_message_on_linked_documents(
                        _("The void of the transaction %s failed.", self.reference)
                    )
            else:  # 'CAPTURE', 'CAPTURE_FAILED'
                _logger.warning(
                    "The capture of the transaction %s failed. reason: %s.",
                    self.reference, refusal_reason,
                )
                if self.source_transaction_id:  # child_tx => The event can't be retried.
                    self._set_error(_(
                        "The capture of the transaction %s failed.", self.reference
                    ))
                else:  # source tx with failed capture stays in its state, could be captured again
                    self._log_message_on_linked_documents(_(
                        "The capture of the transaction %s failed.", self.reference
                    ))
        elif payment_state in const.RESULT_CODES_MAPPING['refused']:
            _logger.warning(
                "the transaction %s was refused. reason: %s",
                self.reference, refusal_reason
            )
            self._set_error(_("Your payment was refused. Please try again."))
        else:  # Classify unsupported payment state as `error` tx state
            _logger.warning(
                "received data for transaction %s with invalid payment state: %s",
                self.reference, payment_state
            )
            self._set_error(
                "Adyen: " + _("Received data with invalid payment state: %s", payment_state)
            )