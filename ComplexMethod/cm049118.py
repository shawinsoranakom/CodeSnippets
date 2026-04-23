def _match_paymob_payment_methods(self, paymob_gateways_data):
        """ Filter gateways available in Paymob to match the payment methods enabled in Odoo.

        This method takes the full list of gateways from Paymob, and while avoiding duplicates,
        returns only those that:

        1. Have a gateway_type mapped to an Odoo payment method code.
        2. Are available for the current provider.
        3. Are not Apple Pay or Google Pay (currently unsupported for mobile-only payments).
        4. Are not a saved card (currently unsupported).
        5. Are not an Authorize/Capture payment methods (currently unsupported).

        :param list[dict] paymob_gateways_data: The gateways data returned by the Paymob API.
        :return: All the matched Paymob gateways' data.
        :rtype: list
        """
        available_payment_method_codes = self.payment_method_ids.mapped('code')
        sorted_gateways_data = sorted(
            paymob_gateways_data,
            key=lambda pm: datetime.fromisoformat(pm['created_at']),
            reverse=True,
        )
        matched_gateways_data = []
        for gateway_data in sorted_gateways_data:
            if not available_payment_method_codes:  # All available payment methods are now matched.
                break
            integration_name = gateway_data.get('integration_name') or ''
            is_apple_pay = 'apple' in integration_name.lower()
            is_google_pay = 'google' in integration_name.lower()
            if is_apple_pay or is_google_pay:
                # Apple Pay and Google Pay are not supported at the moment.
                continue
            gateway_type = gateway_data.get('gateway_type')
            payment_method_code = const.PAYMENT_METHODS_MAPPING.get(gateway_type)
            if payment_method_code == 'card' and (
                # Tokenization and manual capture are not supported at the moment.
                gateway_data['integration_type'] == 'moto' or gateway_data['is_auth']
            ):
                continue
            if payment_method_code in available_payment_method_codes:
                matched_gateways_data.append(gateway_data)
                # In some cases, paymob accounts might have multiple gateway data for the same
                # payment method, only the most recent gateway_data should be considered
                available_payment_method_codes.remove(payment_method_code)
        return matched_gateways_data