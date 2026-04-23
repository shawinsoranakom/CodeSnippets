def _perform_login(self, username, password):
        if len(username) == 10 and username.isdigit() and self._USER_TOKEN is None:
            self.report_login()
            otp_request_json = self._download_json(f'https://b2bapi.zee5.com/device/sendotp_v1.php?phoneno=91{username}',
                                                   None, note='Sending OTP')
            if otp_request_json['code'] == 0:
                self.to_screen(otp_request_json['message'])
            else:
                raise ExtractorError(otp_request_json['message'], expected=True)
            otp_code = self._get_tfa_info('OTP')
            otp_verify_json = self._download_json(f'https://b2bapi.zee5.com/device/verifyotp_v1.php?phoneno=91{username}&otp={otp_code}&guest_token={self._DEVICE_ID}&platform=web',
                                                  None, note='Verifying OTP', fatal=False)
            if not otp_verify_json:
                raise ExtractorError('Unable to verify OTP.', expected=True)
            self._USER_TOKEN = otp_verify_json.get('token')
            if not self._USER_TOKEN:
                raise ExtractorError(otp_request_json['message'], expected=True)
        elif username.lower() == 'token' and try_call(lambda: jwt_decode_hs256(password)):
            self._USER_TOKEN = password
        else:
            raise ExtractorError(self._LOGIN_HINT, expected=True)

        token = jwt_decode_hs256(self._USER_TOKEN)
        if token.get('exp', 0) <= int(time.time()):
            raise ExtractorError('User token has expired', expected=True)
        self._USER_COUNTRY = token.get('current_country')