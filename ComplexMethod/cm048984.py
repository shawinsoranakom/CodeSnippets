def _get_specific_rendering_values(self, processing_values):
        """ Override of `payment` to return Nuvei-specific rendering values.

        Note: self.ensure_one() from `_get_processing_values`

        :param dict processing_values: The generic and specific processing values of the
                                       transaction.
        :return: The dict of provider-specific rendering values.
        :rtype: dict
        """
        if self.provider_code != 'nuvei':
            return super()._get_specific_rendering_values(processing_values)

        first_name, last_name = payment_utils.split_partner_name(self.partner_name)
        if self.payment_method_code in const.FULL_NAME_METHODS and not (first_name and last_name):
            raise UserError(
                "Nuvei: " + _(
                    "%(payment_method)s requires both a first and last name.",
                    payment_method=self.payment_method_id.name,
                )
            )

        # Some payment methods don't support float values, even for currencies that does. Therefore,
        # we must round them.
        is_mandatory_integer_pm = self.payment_method_code in const.INTEGER_METHODS
        rounding = 0 if is_mandatory_integer_pm else self.currency_id.decimal_places
        rounded_amount = float_round(self.amount, rounding, rounding_method='DOWN')

        # Phone numbers need to be standardized and validated.
        phone_number = self.partner_phone and self._phone_format(
            number=self.partner_phone, country=self.partner_country_id, raise_exception=False
        )

        # When a parsing error occurs with Nuvei or the user cancels the order, they do not send the
        # checksum back, as such we need to pass an access token token in the url.
        base_url = self.provider_id.get_base_url()
        return_url = base_url + NuveiController._return_url
        cancel_error_url_params = {
            'tx_ref': self.reference,
            'error_access_token': payment_utils.generate_access_token(self.reference),
        }
        cancel_error_url = f'{return_url}?{urlencode(cancel_error_url_params)}'

        url_params = {
            'address1': self.partner_address or '',
            'city': self.partner_city or '',
            'country': self.partner_country_id.code,
            'currency': self.currency_id.name,
            'email': self.partner_email or '',
            'encoding': 'UTF-8',
            'first_name': first_name[:30],
            'item_amount_1': rounded_amount,
            'item_name_1': self.reference,
            'item_quantity_1': 1,
            'invoice_id': self.reference,
            'last_name': last_name[:40],
            'merchantLocale': self.partner_lang,
            'merchant_id': self.provider_id.nuvei_merchant_identifier,
            'merchant_site_id': self.provider_id.nuvei_site_identifier,
            'payment_method_mode': 'filter',
            'payment_method': const.PAYMENT_METHODS_MAPPING.get(
                self.payment_method_code, self.payment_method_code
            ),
            'phone1': phone_number or '',
            'state': self.partner_state_id.code or '',
            'user_token_id': uuid4(),  # Random string due to some PMs requiring it but not used.
            'time_stamp': self.create_date.strftime('%Y-%m-%d.%H:%M:%S'),
            'total_amount': rounded_amount,
            'version': '4.0.0',
            'zip': self.partner_zip or '',
            'back_url': cancel_error_url,
            'error_url': cancel_error_url,
            'notify_url': base_url + NuveiController._webhook_url,
            'pending_url': return_url,
            'success_url': return_url,
        }

        checksum = self.provider_id._nuvei_calculate_signature(url_params, incoming=False)
        rendering_values = {
            'api_url': self.provider_id._nuvei_get_api_url(),
            'checksum': checksum,
            'url_params': url_params,
        }
        return rendering_values