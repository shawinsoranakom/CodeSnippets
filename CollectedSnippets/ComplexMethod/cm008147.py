def _refresh_access_token(self):
        if not self._oauth_tokens.get(self._REFRESH_TOKEN_KEY):
            self._report_login_error('no_refresh_token')
        if self._token_is_expired(self._REFRESH_TOKEN_KEY):
            self._report_login_error('expired_refresh_token')

        headers = {'Content-Type': 'application/json'}
        if self._is_logged_in:
            headers['Authorization'] = f'Bearer {self._oauth_tokens[self._ACCESS_TOKEN_KEY]}'

        try:
            response = self._download_json(
                f'{self._ACCOUNT_API_BASE}/api/v1/token/refresh', None,
                'Refreshing access token', 'Unable to refresh access token',
                headers={**self._oauth_headers, **headers},
                data=json.dumps({
                    'refreshToken': self._oauth_tokens[self._REFRESH_TOKEN_KEY],
                }, separators=(',', ':')).encode())
        except ExtractorError as e:
            if isinstance(e.cause, HTTPError) and e.cause.status == 401:
                self._oauth_tokens.clear()
                if self._oauth_cache_key == 'cookies':
                    self.cookiejar.clear(domain='.weverse.io', path='/', name=self._ACCESS_TOKEN_KEY)
                    self.cookiejar.clear(domain='.weverse.io', path='/', name=self._REFRESH_TOKEN_KEY)
                else:
                    self.cache.store(self._NETRC_MACHINE, self._oauth_cache_key, self._oauth_tokens)
                self._report_login_error('expired_refresh_token')
            raise

        self._oauth_tokens.update(traverse_obj(response, {
            self._ACCESS_TOKEN_KEY: ('accessToken', {str}, {require('access token')}),
            self._REFRESH_TOKEN_KEY: ('refreshToken', {str}, {require('refresh token')}),
        }))

        if self._oauth_cache_key == 'cookies':
            self._set_cookie('.weverse.io', self._ACCESS_TOKEN_KEY, self._oauth_tokens[self._ACCESS_TOKEN_KEY])
            self._set_cookie('.weverse.io', self._REFRESH_TOKEN_KEY, self._oauth_tokens[self._REFRESH_TOKEN_KEY])
        else:
            self.cache.store(self._NETRC_MACHINE, self._oauth_cache_key, self._oauth_tokens)