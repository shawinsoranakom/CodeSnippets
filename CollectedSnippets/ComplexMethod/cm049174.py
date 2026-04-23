def _xendit_prepare_invoice_request_payload(self):
        """ Create the payload for the invoice request based on the transaction values.

        :return: The request payload.
        :rtype: dict
        """
        base_url = self.provider_id.get_base_url()
        redirect_url = urljoin(base_url, XenditController._return_url)
        access_token = payment_utils.generate_access_token(self.reference, self.amount)
        success_url_params = urls.url_encode({
            'tx_ref': self.reference,
            'access_token': access_token,
            'success': 'true',
        })
        payload = {
            'external_id': self.reference,
            'amount': self._get_rounded_amount(),
            'description': self.reference,
            'customer': {
                'given_names': self.partner_name,
            },
            'success_redirect_url': f'{redirect_url}?{success_url_params}',
            'failure_redirect_url': redirect_url,
            'payment_methods': [const.PAYMENT_METHODS_MAPPING.get(
                self.payment_method_code, self.payment_method_code.upper())
            ],
            'currency': self.currency_id.name,
        }
        # If it's one of FPX methods, assign the payment methods as FPX automatically
        if self.payment_method_code == 'fpx':
            payload['payment_methods'] = const.FPX_METHODS
        # Extra payload values that must not be included if empty.
        if self.partner_email:
            payload['customer']['email'] = self.partner_email
        if phone := self.partner_id.phone:
            payload['customer']['mobile_number'] = phone
        address_details = {}
        if self.partner_city:
            address_details['city'] = self.partner_city
        if self.partner_country_id.name:
            address_details['country'] = self.partner_country_id.name
        if self.partner_zip:
            address_details['postal_code'] = self.partner_zip
        if self.partner_state_id.name:
            address_details['state'] = self.partner_state_id.name
        if self.partner_address:
            address_details['street_line1'] = self.partner_address
        if address_details:
            payload['customer']['addresses'] = [address_details]

        return payload