def _snailmail_print_valid_address(self):
        """
        get response
        {
            'request_code': RESPONSE_OK, # because we receive 200 if good or fail
            'total_cost': total_cost,
            'credit_error': credit_error,
            'request': {
                'documents': documents,
                'options': options
                }
            }
        }
        """
        endpoint = self.env['ir.config_parameter'].sudo().get_param('snailmail.endpoint', DEFAULT_ENDPOINT)
        timeout = int(self.env['ir.config_parameter'].sudo().get_param('snailmail.timeout', DEFAULT_TIMEOUT))
        params = self._snailmail_create('print')
        try:
            response = iap_tools.iap_jsonrpc(endpoint + PRINT_ENDPOINT, params=params, timeout=timeout)
        except AccessError as ae:
            for doc in params['documents']:
                letter = self.browse(doc['letter_id'])
                letter.state = 'error'
                letter.error_code = 'UNKNOWN_ERROR'
            raise ae
        for doc in response['request']['documents']:
            if doc.get('sent') and response['request_code'] == 200:
                self.env['iap.account']._send_success_notification(
                    message=_("Snail Mails are successfully sent"))
                note = _('The document was correctly sent by post.<br>The tracking id is %s', doc['send_id'])
                letter_data = {'info_msg': note, 'state': 'sent', 'error_code': False}
                notification_data = {
                    'notification_status': 'sent',
                    'failure_type': False,
                    'failure_reason': False,
                }
            else:
                error = doc['error'] if response['request_code'] == 200 else response['reason']

                if error == 'CREDIT_ERROR':
                    self.env['iap.account']._send_no_credit_notification(
                        service_name='snailmail',
                        title=_("Not enough credits for Snail Mail"))
                note = _('An error occurred when sending the document by post.<br>Error: %s', self._get_error_message(error))
                letter_data = {
                    'info_msg': note,
                    'state': 'error',
                    'error_code': error if error in ERROR_CODES else 'UNKNOWN_ERROR'
                }
                notification_data = {
                    'notification_status': 'exception',
                    'failure_type': self._get_failure_type(error),
                    'failure_reason': note,
                }

            letter = self.browse(doc['letter_id'])
            letter.write(letter_data)
            letter.notification_ids.sudo().write(notification_data)
        self.message_id._notify_message_notification_update()