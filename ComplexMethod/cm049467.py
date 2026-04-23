def razorpay_fetch_payment_status(self, data):
        razorpay = RazorpayPosRequest(self)
        body = razorpay._razorpay_get_request_parameters()
        body.update({'origP2pRequestId': data.get('p2pRequestId')})
        response = razorpay._call_razorpay(endpoint='status', payload=body)
        if response.get('success') and not response.get('errorCode'):
            payment_status = response.get('status')
            payment_messageCode = response.get('messageCode')
            if payment_status == 'AUTHORIZED' and payment_messageCode == 'P2P_DEVICE_TXN_DONE':
                return {
                    'status': response.get('status'),
                    'authCode': response.get('authCode'),
                    'cardLastFourDigit': response.get('cardLastFourDigit'),
                    'externalRefNumber': response.get('externalRefNumber'),
                    'reverseReferenceNumber': response.get('reverseReferenceNumber'),
                    'txnId': response.get('txnId'),
                    'paymentMode': response.get('paymentMode'),
                    'paymentCardType': response.get('paymentCardType'),
                    'paymentCardBrand': response.get('paymentCardBrand'),
                    'nameOnCard': response.get('nameOnCard'),
                    'acquirerCode': response.get('acquirerCode'),
                    'createdTime': response.get('createdTime'),
                    'p2pRequestId': response.get('p2pRequestId'),
                    'settlementStatus': response.get('settlementStatus'),
                }
            elif payment_status in ['VOIDED', 'AUTHORIZED_REFUNDED'] and payment_messageCode == 'P2P_DEVICE_TXN_DONE':
                return {
                    'status': payment_status,
                    'settlementStatus': response.get('settlementStatus'),
                }
            elif payment_status == 'FAILED' or payment_messageCode == 'P2P_DEVICE_CANCELED':
                return {'error': str(response.get('message', _('Razorpay POS transaction failed'))),
                        'payment_messageCode': payment_messageCode}
            elif payment_messageCode in ['P2P_DEVICE_RECEIVED', 'P2P_DEVICE_SENT', 'P2P_STATUS_QUEUED']:
                return {'status': payment_messageCode.split('_')[-1]}
        default_error_msg = _('Razorpay POS payment status request expected errorCode not found in the response')
        error = response.get('errorMessage') or default_error_msg
        return {'error': str(error)}