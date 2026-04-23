def _worldline_create_checkout_session(self):
        """ Create a hosted checkout session and return the response data.

        :return: The hosted checkout session data.
        :rtype: dict
        """
        self.ensure_one()

        base_url = self.provider_id.get_base_url()
        return_route = WorldlineController._return_url
        return_url_params = url_encode({'provider_id': str(self.provider_id.id)})
        return_url = f'{urls.urljoin(base_url, return_route)}?{return_url_params}'
        first_name, last_name = payment_utils.split_partner_name(self.partner_name)
        payload = {
            'hostedCheckoutSpecificInput': {
                'locale': self.partner_lang or '',
                'returnUrl': return_url,
                'showResultPage': False,
            },
            'order': {
                'amountOfMoney': {
                    'amount': payment_utils.to_minor_currency_units(self.amount, self.currency_id),
                    'currencyCode': self.currency_id.name,
                },
                'customer': {  # required to create a token and for some redirected payment methods
                    'billingAddress': {
                        'city': self.partner_city or '',
                        'countryCode': self.partner_country_id.code or '',
                        'state': self.partner_state_id.name or '',
                        'street': self.partner_address or '',
                        'zip': self.partner_zip or '',
                    },
                    'contactDetails': {
                        'emailAddress': self.partner_email or '',
                        'phoneNumber': self.partner_phone or '',
                    },
                    'personalInformation': {
                        'name': {
                            'firstName': first_name or '',
                            'surname': last_name or '',
                        },
                    },
                },
                'references': {
                    'descriptor': self.reference,
                    'merchantReference': self.reference,
                },
            },
        }
        if self.payment_method_id.code in const.REDIRECT_PAYMENT_METHODS:
            payload['redirectPaymentMethodSpecificInput'] = {
                'requiresApproval': False,  # Force the capture.
                'paymentProductId': const.PAYMENT_METHODS_MAPPING[self.payment_method_id.code],
                'redirectionData': {
                    'returnUrl': return_url,
                },
            }
        else:
            payload['cardPaymentMethodSpecificInput'] = {
                'authorizationMode': 'SALE',  # Force the capture.
                'tokenize': self.tokenize,
            }
            if not self.payment_method_id.brand_ids and self.payment_method_id.code != 'card':
                worldline_code = const.PAYMENT_METHODS_MAPPING.get(self.payment_method_id.code, 0)
                payload['cardPaymentMethodSpecificInput']['paymentProductId'] = worldline_code
            else:
                payload['hostedCheckoutSpecificInput']['paymentProductFilters'] = {
                    'restrictTo': {
                        'groups': ['cards'],
                    },
                }

        checkout_session_data = self._send_api_request('POST', 'hostedcheckouts', json=payload)

        return checkout_session_data