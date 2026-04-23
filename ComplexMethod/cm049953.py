def proxy_adyen_request(self, data, operation=False):
        ''' Necessary because Adyen's endpoints don't have CORS enabled '''
        self.ensure_one()
        if not self.env.su and not self.env.user.has_group('point_of_sale.group_pos_user'):
            raise AccessDenied()
        if not data:
            raise UserError(_('Invalid Adyen request'))

        if 'SaleToPOIRequest' in data and data['SaleToPOIRequest']['MessageHeader']['MessageCategory'] == 'Payment' and 'PaymentRequest' in data['SaleToPOIRequest']:  # Clear only if it is a payment request
            self.sudo().adyen_latest_response = ''  # avoid handling old responses multiple times

        if not operation:
            operation = 'terminal_request'

        # These checks are not optimal. This RPC method should be changed.

        is_capture_data = operation == 'capture' and hasattr(self, 'adyen_merchant_account') and self._is_valid_adyen_request_data(data, {
            'originalReference': UNPREDICTABLE_ADYEN_DATA,
            'modificationAmount': {
                'value': UNPREDICTABLE_ADYEN_DATA,
                'currency': UNPREDICTABLE_ADYEN_DATA,
            },
            'merchantAccount': self.adyen_merchant_account,
        })

        is_adjust_data = operation == 'adjust' and hasattr(self, 'adyen_merchant_account') and self._is_valid_adyen_request_data(data, {
            'originalReference': UNPREDICTABLE_ADYEN_DATA,
            'modificationAmount': {
                'value': UNPREDICTABLE_ADYEN_DATA,
                'currency': UNPREDICTABLE_ADYEN_DATA,
            },
            'merchantAccount': self.adyen_merchant_account,
            'additionalData': {
                'industryUsage': 'DelayedCharge',
            },
        })

        is_cancel_data = operation == 'terminal_request' and self._is_valid_adyen_request_data(data, {
            'SaleToPOIRequest': {
                'MessageHeader': self._get_expected_message_header('Abort'),
                'AbortRequest': {
                    'AbortReason': 'MerchantAbort',
                    'MessageReference': {
                        'MessageCategory': 'Payment',
                        'SaleID': UNPREDICTABLE_ADYEN_DATA,
                        'ServiceID': UNPREDICTABLE_ADYEN_DATA,
                    },
                },
            },
        })

        is_payment_request_with_acquirer_data = operation == 'terminal_request' and self._is_valid_adyen_request_data(data, self._get_expected_payment_request(True))

        if is_payment_request_with_acquirer_data:
            parsed_sale_to_acquirer_data = parse_qs(data['SaleToPOIRequest']['PaymentRequest']['SaleData']['SaleToAcquirerData'])
            valid_acquirer_data = self._get_valid_acquirer_data()
            is_payment_request_with_acquirer_data = len(parsed_sale_to_acquirer_data.keys()) <= len(valid_acquirer_data.keys())
            if is_payment_request_with_acquirer_data:
                for key, values in parsed_sale_to_acquirer_data.items():
                    if len(values) != 1:
                        is_payment_request_with_acquirer_data = False
                        break
                    value = values[0]
                    valid_value = valid_acquirer_data.get(key)
                    if valid_value == UNPREDICTABLE_ADYEN_DATA:
                        continue
                    if value != valid_value:
                        is_payment_request_with_acquirer_data = False
                        break

        is_payment_request_without_acquirer_data = operation == 'terminal_request' and self._is_valid_adyen_request_data(data, self._get_expected_payment_request(False))

        if not is_payment_request_without_acquirer_data and not is_payment_request_with_acquirer_data and not is_adjust_data and not is_cancel_data and not is_capture_data:
            raise UserError(_('Invalid Adyen request'))

        if is_payment_request_with_acquirer_data or is_payment_request_without_acquirer_data:
            acquirer_data = data['SaleToPOIRequest']['PaymentRequest']['SaleData'].get('SaleToAcquirerData')
            msg_header = data['SaleToPOIRequest']['MessageHeader']
            metadata = 'metadata.pos_hmac=' + self._get_hmac(msg_header['SaleID'], msg_header['ServiceID'], msg_header['POIID'], data['SaleToPOIRequest']['PaymentRequest']['SaleData']['SaleTransactionID']['TransactionID'])

            data['SaleToPOIRequest']['PaymentRequest']['SaleData']['SaleToAcquirerData'] = acquirer_data + '&' + metadata if acquirer_data else metadata

        return self._proxy_adyen_request_direct(data, operation)