def _perform_login(self, username, password):
        if self._get_cookies(self._API_BASE_URL).get('rt_access_token'):
            return

        try:
            self._download_json(
                'https://auth.roosterteeth.com/oauth/token',
                None, 'Logging in', data=urlencode_postdata({
                    'client_id': '4338d2b4bdc8db1239360f28e72f0d9ddb1fd01e7a38fbb07b4b1f4ba4564cc5',
                    'grant_type': 'password',
                    'username': username,
                    'password': password,
                }))
        except ExtractorError as e:
            msg = 'Unable to login'
            if isinstance(e.cause, HTTPError) and e.cause.status == 401:
                resp = self._parse_json(e.cause.response.read().decode(), None, fatal=False)
                if resp:
                    error = resp.get('extra_info') or resp.get('error_description') or resp.get('error')
                    if error:
                        msg += ': ' + error
            self.report_warning(msg)