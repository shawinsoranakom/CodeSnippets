def _apply_updates(self, payment_data):
        """Override of `payment` to update the transaction based on the payment data."""
        if self.provider_code != 'razorpay':
            return super()._apply_updates(payment_data)

        if 'id' in payment_data:  # We have the full entity data (S2S request or webhook).
            entity_data = payment_data
        else:  # The payment data are not complete (Payments made by a token).
            # Fetch the full payment data.
            try:
                entity_data = self._send_api_request(
                    'GET', f'payments/{payment_data["razorpay_payment_id"]}'
                )
            except ValidationError as e:
                self._set_error(str(e))
                return

        # Update the provider reference.
        entity_id = entity_data.get('id')
        if not entity_id:
            self._set_error(_("Received data with missing entity id."))
            return

        # One reference can have multiple entity ids as Razorpay allows retry on payment failure.
        # Making sure the last entity id is the one we have in the provider reference.
        allowed_to_modify = self.state not in ('done', 'authorized')
        if allowed_to_modify:
            self.provider_reference = entity_id

        # Update the payment method.
        payment_method_type = entity_data.get('method', '')
        if payment_method_type == 'card':
            payment_method_type = entity_data.get('card', {}).get('network', '').lower()
        payment_method = self.env['payment.method']._get_from_code(
            payment_method_type, mapping=const.PAYMENT_METHODS_MAPPING
        )
        if allowed_to_modify and payment_method:
            self.payment_method_id = payment_method

        # Update the payment state.
        entity_status = entity_data.get('status')
        if not entity_status:
            self._set_error(_("Received data with missing status."))

        if entity_status in const.PAYMENT_STATUS_MAPPING['pending']:
            self._set_pending()
        elif entity_status in const.PAYMENT_STATUS_MAPPING['authorized']:
            if self.provider_id.capture_manually:
                self._set_authorized()
        elif entity_status in const.PAYMENT_STATUS_MAPPING['done']:
            if (
                not self.token_id
                and entity_data.get('token_id')
                and self.provider_id.allow_tokenization
            ):
                # In case the tokenization was requested on provider side not from odoo form.
                self.tokenize = True
            self._set_done()

            # Immediately post-process the transaction if it is a refund, as the post-processing
            # will not be triggered by a customer browsing the transaction from the portal.
            if self.operation == 'refund':
                self.env.ref('payment.cron_post_process_payment_tx')._trigger()
        elif entity_status in const.PAYMENT_STATUS_MAPPING['error']:
            _logger.warning(
                "The transaction %s underwent an error. Reason: %s",
                self.reference, entity_data.get('error_description')
            )
            self._set_error(
                _("An error occurred during the processing of your payment. Please try again.")
            )
        else:  # Classify unsupported payment status as the `error` tx state.
            _logger.warning(
                "Received data for transaction %s with invalid payment status: %s.",
                self.reference, entity_status
            )
            self._set_error(
                "Razorpay: " + _("Received data with invalid status: %s", entity_status)
            )