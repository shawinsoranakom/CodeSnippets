def _send_sms_batch(self, messages, delivery_reports_url=False):
        """ Send a batch of SMS using twilio.
        See params and returns in original method sms/tools/sms_api.py
        In addition to the uuid and state, we add the sms_twilio_sid to the returns (one per sms)
        """
        # Use a session as we have to sequentially call twilio, might save time
        session = requests.Session()

        res = []
        for message in messages:
            body = message.get('content') or ''
            for number_info in message.get('numbers') or []:
                uuid = number_info['uuid']
                response = self._sms_twilio_send_request(session, number_info['number'], body, uuid)
                fields_values = {
                    'failure_reason':  _("Unknown failure at sending, please contact Odoo support"),
                    'state': 'server_error',
                    'uuid': uuid,
                }
                if response is not None:
                    response_json = response.json()
                    if not response.ok or response_json.get('error'):
                        failure_type = self._twilio_error_code_to_odoo_state(response_json)
                        error_message = response_json.get('message') or response_json.get('error_message') or self._get_sms_api_error_messages().get(failure_type)
                        fields_values.update({
                            'failure_reason': error_message,
                            'failure_type': failure_type,
                            'state': failure_type,
                        })
                    else:
                        fields_values.update({
                            'failure_reason': False,
                            'failure_type': False,
                            'sms_twilio_sid': response_json.get('sid'),
                            'state': 'sent',
                        })
                res.append(fields_values)
        return res