def _login(self):
        username, password = self._get_login_info()
        if username is None:
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
            if isinstance(e.cause, compat_HTTPError) and e.cause.code == 401:
                resp = self._parse_json(e.cause.read().decode(), None, fatal=False)
                if resp:
                    error = resp.get('extra_info') or resp.get('error_description') or resp.get('error')
                    if error:
                        msg += ': ' + error
            self.report_warning(msg)