def _stripe_get_inline_form_values(
        self, amount, currency, partner_id, is_validation, payment_method_sudo=None, **kwargs
    ):
        """Return a serialized JSON of the required values to render the inline form.

        Note: `self.ensure_one()`

        :param float amount: The amount in major units, to convert in minor units.
        :param res.currency currency: The currency of the transaction.
        :param int partner_id: The partner of the transaction, as a `res.partner` id.
        :param bool is_validation: Whether the operation is a validation.
        :param payment.method payment_method_sudo: The sudoed payment method record to which the
                                                   inline form belongs.
        :return: The JSON serial of the required values to render the inline form.
        :rtype: str
        """
        self.ensure_one()

        if not is_validation:
            currency_name = currency and currency.name.lower()
        else:
            currency_name = self.with_context(
                validation_pm=payment_method_sudo  # Will be converted to a kwarg in master.
            )._get_validation_currency().name.lower()
        partner = self.env['res.partner'].with_context(show_address=1).browse(partner_id).exists()
        inline_form_values = {
            'publishable_key': self._stripe_get_publishable_key(),
            'currency_name': currency_name,
            'minor_amount': amount and payment_utils.to_minor_currency_units(
                amount,
                currency,
                arbitrary_decimal_number=const.CURRENCY_DECIMALS.get(currency.name),
            ),
            'capture_method': 'manual' if self.capture_manually else 'automatic',
            'billing_details': {
                'name': partner.name or '',
                'email': partner.email or '',
                'phone': partner.phone or '',
                'address': {
                    'line1': partner.street or '',
                    'line2': partner.street2 or '',
                    'city': partner.city or '',
                    'state': partner.state_id.code or '',
                    'country': partner.country_id.code or '',
                    'postal_code': partner.zip or '',
                },
            },
            'is_tokenization_required': (
                self.allow_tokenization
                and self._is_tokenization_required(**kwargs)
                and payment_method_sudo.support_tokenization
            ),
            'payment_methods_mapping': const.PAYMENT_METHODS_MAPPING,
        }
        return json.dumps(inline_form_values)