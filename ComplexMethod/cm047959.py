def _request_handler(cls, session, request, **kwargs):
        url = request.url
        matching = cls.twilio_request_re.match(url)
        if matching:
            _sid = matching.group(1)
            right_part = matching.group(2)
            response = Response()
            response.status_code = 200
            if right_part == "IncomingPhoneNumbers.json":
                response.json = lambda: {
                    'incoming_phone_numbers': [
                        {'phone_number': '+32455998877'},
                        {'phone_number': '+32455665544'},
                    ],
                }
                return response
            elif right_part == "Messages.json":
                error_type = cls.mock_error_number_to_type.get(cls.mock_number) or cls.mock_error_type
                if not error_type and not cls.mock_number:
                    error_type = "sms_number_missing"
                error_codes = {
                    'wrong_number_format': 21211,
                    'sms_number_missing': 21604,
                    'twilio_acc_unverified': 21608,
                    'twilio_callback': 21609,
                    'unknown': 1,
                    'other': 1,
                }
                if not error_type:
                    request_send_ok_json = cls.request_send_ok_json.copy()
                    request_send_ok_json['body'] = cls.mock_body or 'body'
                    request_send_ok_json['sid'] = f'twilio_{cls.mock_company.name}_{cls.mock_sms_uuid}' if cls.mock_sms_uuid else 'SMFake'
                    request_send_ok_json['to_number'] = cls.mock_number or 'to_number'
                    response.json = lambda: request_send_ok_json
                else:
                    if error_type not in error_codes:
                        raise ValueError('Unsupported error code')
                    error_code = error_codes.get(error_type) if error_type else False

                    request_send_nok_json = cls.request_send_nok_json.copy()
                    request_send_nok_json['body'] = cls.mock_body or 'body'
                    request_send_nok_json['code'] = error_code
                    request_send_nok_json['to_number'] = cls.mock_number or 'to_number'
                    response.json = lambda: request_send_nok_json
                    response.status_code = 400
                return response
        return super()._request_handler(session, request, **kwargs)