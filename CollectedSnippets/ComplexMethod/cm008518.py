def _real_initialize(self):
        self.token = None

        cookies = self._get_cookies('https://7plus.com.au')
        api_key = next((x for x in cookies if x.startswith('glt_')), '')[4:]
        if not api_key:  # Cookies are signed out, skip login
            return

        login_resp = self._download_json(
            'https://login.7plus.com.au/accounts.getJWT', None, 'Logging in', fatal=False,
            query={
                'APIKey': api_key,
                'sdk': 'js_latest',
                'login_token': cookies[f'glt_{api_key}'].value,
                'authMode': 'cookie',
                'pageURL': 'https://7plus.com.au/',
                'sdkBuild': '12471',
                'format': 'json',
            }) or {}

        if 'errorMessage' in login_resp:
            self.report_warning(f'Unable to login: 7plus said: {login_resp["errorMessage"]}')
            return
        id_token = login_resp.get('id_token')
        if not id_token:
            self.report_warning('Unable to login: Could not extract id token')
            return

        token_resp = self._download_json(
            'https://7plus.com.au/auth/token', None, 'Getting auth token', fatal=False,
            headers={'Content-Type': 'application/json'}, data=json.dumps({
                'idToken': id_token,
                'platformId': 'web',
                'regSource': '7plus',
            }).encode()) or {}
        self.token = token_resp.get('token')
        if not self.token:
            self.report_warning('Unable to log in: Could not extract auth token')