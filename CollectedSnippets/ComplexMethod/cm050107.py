def _apply_updates(self, payment_data):
        """Override of `payment` to update the transaction based on the payment data."""
        if self.provider_code != 'mercado_pago':
            return super()._apply_updates(payment_data)

        # Update the provider reference.
        payment_id = payment_data.get('id')
        if not payment_id:
            self._set_error(_("Received data with missing payment id."))
            return
        self.provider_reference = payment_id

        # Update the payment method.
        payment_method_type = payment_data.get('payment_type_id', '')
        for odoo_code, mp_codes in const.PAYMENT_METHODS_MAPPING.items():
            if any(payment_method_type == mp_code for mp_code in mp_codes.split(',')):
                payment_method_type = odoo_code
                break
        if payment_method_type == 'card':
            payment_method_code = payment_data.get('payment_method_id')
        else:
            payment_method_code = payment_method_type
        payment_method = self.env['payment.method']._get_from_code(
            payment_method_code, mapping=const.PAYMENT_METHODS_MAPPING
        )
        # Fall back to "unknown" if the payment method is not found (and if "unknown" is found), as
        # the user might have picked a different payment method than on Odoo's payment form.
        if not payment_method:
            payment_method = self.env['payment.method'].search([('code', '=', 'unknown')], limit=1)
        self.payment_method_id = payment_method or self.payment_method_id

        # Update the payment state.
        payment_status = payment_data.get('status')
        if not payment_status:
            self._set_error(_("Received data with missing status."))
            return

        if payment_status in const.TRANSACTION_STATUS_MAPPING['pending']:
            self._set_pending()
        elif payment_status in const.TRANSACTION_STATUS_MAPPING['done']:
            self._set_done()
        elif payment_status in const.TRANSACTION_STATUS_MAPPING['canceled']:
            self._set_canceled()
        elif payment_status in const.TRANSACTION_STATUS_MAPPING['error']:
            status_detail = payment_data.get('status_detail')
            _logger.warning(
                "Received data for transaction %s with status %s and error code: %s.",
                self.reference, payment_status, status_detail
            )
            error_message = self._mercado_pago_get_error_msg(status_detail)
            self._set_error(error_message)
        else:  # Classify unsupported payment status as the `error` tx state.
            _logger.warning(
                "Received data for transaction %s with invalid payment status: %s.",
                self.reference, payment_status
            )
            self._set_error(_("Received data with invalid status: %s.", payment_status))