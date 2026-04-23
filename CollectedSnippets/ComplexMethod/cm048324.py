def _stripe_prepare_payment_intent_payload(self):
        """ Prepare the payload for the creation of a PaymentIntent object in Stripe format.

        Note: This method serves as a hook for modules that would fully implement Stripe Connect.

        :return: The Stripe-formatted payload for the PaymentIntent request.
        :rtype: dict
        """
        ppm_code = self.payment_method_id.primary_payment_method_id.code
        payment_method_type = ppm_code or self.payment_method_code
        payment_intent_payload = {
            'amount': payment_utils.to_minor_currency_units(
                self.amount,
                self.currency_id,
                arbitrary_decimal_number=const.CURRENCY_DECIMALS.get(self.currency_id.name),
            ),
            'currency': self.currency_id.name.lower(),
            'description': self.reference,
            'capture_method': 'manual' if self.provider_id.capture_manually else 'automatic',
            'payment_method_types[]': const.PAYMENT_METHODS_MAPPING.get(
                payment_method_type, payment_method_type
            ),
            'expand[]': 'payment_method',
            **stripe_utils.include_shipping_address(self),
        }
        if self.operation in ['online_token', 'offline']:
            if not self.token_id.stripe_payment_method:  # Pre-SCA token, migrate it.
                self.token_id._stripe_sca_migrate_customer()

            payment_intent_payload.update({
                'confirm': True,
                'customer': self.token_id.provider_ref,
                'off_session': True,
                'payment_method': self.token_id.stripe_payment_method,
                'mandate': self.token_id.stripe_mandate or None,
            })
        else:
            customer = self._stripe_create_customer()
            payment_intent_payload['customer'] = customer['id']
            if self.tokenize:
                payment_intent_payload['setup_future_usage'] = 'off_session'
                if self.currency_id.name in const.INDIAN_MANDATES_SUPPORTED_CURRENCIES:
                    payment_intent_payload.update(**self._stripe_prepare_mandate_options())
        return payment_intent_payload