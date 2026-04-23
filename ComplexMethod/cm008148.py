def _perform_login(self, username, password):
        if self._is_logged_in:
            return

        if username.partition('+')[0] != self._OAUTH_PREFIX:
            self._report_login_error('invalid_username')

        self._oauth_tokens.update(self.cache.load(self._NETRC_MACHINE, self._oauth_cache_key, default={}))
        if self._is_logged_in and self._access_token_is_valid():
            return

        rt_key = self._REFRESH_TOKEN_KEY
        if not self._oauth_tokens.get(rt_key) or self._token_is_expired(rt_key):
            if try_call(lambda: jwt_decode_hs256(password)['scope']) != 'refresh':
                self._report_login_error('invalid_password')
            self._oauth_tokens[rt_key] = password

        self._refresh_access_token()