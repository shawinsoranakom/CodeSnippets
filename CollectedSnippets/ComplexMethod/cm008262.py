def _perform_login(self, username, password):
        if not self._refresh_token:
            self._refresh_token, self._access_token = self.cache.load(
                self._NETRC_MACHINE, 'token_data', default=[None, None])

        if self._refresh_token and self._access_token:
            self.write_debug('Using cached refresh token')
            if not self._claims_token:
                self._claims_token = self.cache.load(self._NETRC_MACHINE, 'claims_token')
            return

        try:
            self._call_oauth_api({
                'grant_type': 'password',
                'username': username,
                'password': password,
            }, note='Logging in')
        except ExtractorError as e:
            if isinstance(e.cause, HTTPError) and e.cause.status == 400:
                raise ExtractorError('Invalid username and/or password', expected=True)
            raise