def _perform_login(self, username, password):
        self.report_login()

        if username == 'refresh':
            self._refresh_token = password
            self._fetch_new_tokens()

        if username == 'token':
            if not traverse_obj(password, {jwt_decode_hs256}):
                raise ExtractorError(
                    f'The access token passed to yt-dlp is not valid. {self._LOGIN_HINT}', expected=True)
            self._set_access_token(password)
            self._cache_tokens()

        if username in ('refresh', 'token'):
            if self.get_param('cachedir') is not False:
                token_type = 'access' if username == 'token' else 'refresh'
                self.to_screen(f'Your {token_type} token has been cached to disk. To use the cached '
                               'token next time, pass  --username cache  along with any password')
            return

        if username != 'cache':
            raise ExtractorError(
                'Login with username and password is no longer supported '
                f'for this site. {self._LOGIN_HINT}, {self._REFRESH_HINT}', expected=True)

        # Try cached access_token
        cached_tokens = self.cache.load(self._NETRC_MACHINE, 'tokens', default={})
        self._set_access_token(cached_tokens.get('access_token'))
        self._refresh_token = cached_tokens.get('refresh_token')
        if not self._access_token_is_expired:
            return

        # Try cached refresh_token
        self._fetch_new_tokens(invalidate=True)