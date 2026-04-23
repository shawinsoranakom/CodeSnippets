def _validate_amount(self, payment_data):
        """Ensure that the transaction's amount and currency match the ones from the payment data.

        Validation transactions and transactions for which providers opt out of the amount check are
        skipped.

        :param dict payment_data: The payment data sent by the provider.
        :return: None
        """
        self.ensure_one()

        if self.operation == 'validation':
            return  # Skip validation for $0-auth transactions.

        amount_data = self._extract_amount_data(payment_data)
        if amount_data is None:
            return  # Skip validation for transactions where the provider opts out of amount check.

        amount = amount_data['amount']
        currency_code = amount_data['currency_code']
        precision_digits = amount_data.get('precision_digits')

        if not amount or not currency_code:
            error_message = _("The amount or currency is missing from the payment data.")
            self._set_error(error_message)
            return

        # Negate the amount for refunds, as refunds have a negative amount in Odoo, but all
        # providers send a positive one.
        if self.operation == 'refund':
            amount = -amount
        if precision_digits is None:
            precision_digits = CURRENCY_MINOR_UNITS.get(
                self.currency_id.name, self.currency_id.decimal_places
            )
        tx_amount = float_round(
            self.amount, precision_digits=precision_digits, rounding_method='DOWN'
        )
        if self.currency_id.compare_amounts(amount, tx_amount) != 0:
            error_message = _(
                "The amount from the payment data doesn't match the one from the transaction."
            )
            self._set_error(error_message)
            return

        if currency_code != self.currency_id.name:
            error_message = _(
                "The currency from the payment data doesn't match the one from the transaction."
            )
            self._set_error(error_message)