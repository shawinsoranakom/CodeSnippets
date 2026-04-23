def _paymob_prepare_payment_request_payload(self):
        """ Create the payload for the payment request based on the transaction values.

        :return: The request payload.
        :rtype: dict
        """
        partner_first_name, partner_last_name = payment_utils.split_partner_name(self.partner_name)
        payment_method_codes = [self.payment_method_code]

        # If the user selects the Oman Net Payment Method to pay, Integration ID for both Card and
        # Oman Net Integrations should be passed in the Intention API. The transaction will fail if
        # you only pass Oman Net Integration ID.
        if self.payment_method_code == 'omannet':
            payment_method_codes.append('card')

        # Suffix to all payment methods with the environment.
        environment = 'live' if self.provider_id.state == 'enabled' else 'test'
        payment_method_codes = [
            f'{code.replace("_", "")}{environment}' for code in payment_method_codes
        ]

        base_url = self.get_base_url()
        redirect_url = urls.urljoin(base_url, PaymobController._return_url)
        webhook_url = urls.urljoin(base_url, PaymobController._webhook_url)

        return {
            'special_reference': self.reference,
            'amount': payment_utils.to_minor_currency_units(self.amount, self.currency_id),
            'currency': self.currency_id.name,
            'payment_methods': payment_method_codes,
            'notification_url': webhook_url,
            'redirection_url': redirect_url,
            'billing_data': {
                'first_name': partner_first_name or partner_last_name or '',
                'last_name': partner_last_name or '',
                'email': self.partner_email or '',
                'street': self.partner_address or '',
                'state': self.partner_state_id.name or '',
                'phone_number': (self.partner_phone or '').replace(' ', ''),
                'country': self.partner_country_id.code or '',
            },
        }