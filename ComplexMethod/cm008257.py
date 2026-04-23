def _get_token(self, xid):
        cookies = self._get_dailymotion_cookies()
        token = self._get_cookie_value(cookies, 'access_token') or self._get_cookie_value(cookies, 'client_token')
        if token:
            return token

        data = {
            'client_id': 'f1a362d288c1b98099c7',
            'client_secret': 'eea605b96e01c796ff369935357eca920c5da4c5',
        }
        username, password = self._get_login_info()
        if username:
            data.update({
                'grant_type': 'password',
                'password': password,
                'username': username,
            })
        else:
            data['grant_type'] = 'client_credentials'
        try:
            token = self._download_json(
                'https://graphql.api.dailymotion.com/oauth/token',
                None, 'Downloading Access Token',
                data=urlencode_postdata(data))['access_token']
        except ExtractorError as e:
            if isinstance(e.cause, HTTPError) and e.cause.status == 400:
                raise ExtractorError(self._parse_json(
                    e.cause.response.read().decode(), xid)['error_description'], expected=True)
            raise
        self._set_dailymotion_cookie('access_token' if username else 'client_token', token)
        return token