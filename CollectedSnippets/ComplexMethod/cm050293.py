def _extract_token_values(self, payment_data):
        """Override of `payment` to return token data based on Razorpay data.

        Note: self.ensure_one() from :meth: `_tokenize`

        :param dict payment_data: The payment data sent by the provider.
        :return: Data to create a token.
        :rtype: dict
        """
        if self.provider_code != 'razorpay':
            return super()._extract_token_values(payment_data)

        has_token_data = payment_data.get('token_id')
        if self.token_id or not self.provider_id.allow_tokenization or not has_token_data:
            return {}

        pm_code = (self.payment_method_id.primary_payment_method_id or self.payment_method_id).code
        if pm_code == 'card':
            details = payment_data.get('card', {}).get('last4')
        elif pm_code == 'upi':
            temp_vpa = payment_data.get('vpa')
            details = temp_vpa[temp_vpa.find('@') - 1:]
        else:
            details = pm_code
        return {
            'payment_details': details,
            # Razorpay requires both the customer ID and the token ID which are extracted from here.
            'provider_ref': f'{payment_data["customer_id"]},{payment_data["token_id"]}',
        }