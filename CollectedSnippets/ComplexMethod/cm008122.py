def _perform_login(self, username, password):
        try:
            access_token = (self._download_json(
                self._API_BASE_URL + 'authentication/login', None,
                'Logging in', self._LOGIN_ERR_MESSAGE, fatal=False,
                data=urlencode_postdata({
                    'password': password,
                    'rememberMe': False,
                    'source': 'Web',
                    'username': username,
                })) or {}).get('accessToken')
            if access_token:
                self._HEADERS['Authorization'] = f'Bearer {access_token}'
        except ExtractorError as e:
            message = None
            if isinstance(e.cause, HTTPError) and e.cause.status == 401:
                resp = self._parse_json(
                    e.cause.response.read().decode(), None, fatal=False) or {}
                message = resp.get('message') or resp.get('code')
            self.report_warning(message or self._LOGIN_ERR_MESSAGE)