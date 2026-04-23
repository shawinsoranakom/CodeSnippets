def _fetch_new_tokens(self, invalidate=False):
        if invalidate:
            self.report_warning('Access token has been invalidated')
            self._set_access_token(None)

        if not self._access_token_is_expired:
            return

        if not self._refresh_token:
            self._set_access_token(None)
            self._cache_tokens()
            raise ExtractorError(
                'Access token has expired or been invalidated. '
                'Get a new "access_token_production" value from your browser '
                f'and try again, {self._REFRESH_HINT}', expected=True)

        # If we only have a refresh token, we need a temporary "initial token" for the refresh flow
        bearer_token = self._access_token or self._download_json(
            self._OAUTH_URL, None, 'Obtaining initial token', 'Unable to obtain initial token',
            data=urlencode_postdata({
                'affiliate': 'none',
                'grant_type': 'device',
                'device_vendor': 'unknown',
                # device_model 'Safari' gets split streams of 4K/HEVC video and lossless/FLAC audio,
                # but this is no longer effective since actual login is not possible anymore
                'device_model': 'unknown',
                'app_id': self._CLIENT_ID,
                'app_distributor': 'berlinphil',
                'app_version': '1.95.0',
                'client_secret': self._CLIENT_SECRET,
            }), headers=self._OAUTH_HEADERS)['access_token']

        try:
            response = self._download_json(
                self._OAUTH_URL, None, 'Refreshing token', 'Unable to refresh token',
                data=urlencode_postdata({
                    'grant_type': 'refresh_token',
                    'refresh_token': self._refresh_token,
                    'client_id': self._CLIENT_ID,
                    'client_secret': self._CLIENT_SECRET,
                }), headers={
                    **self._OAUTH_HEADERS,
                    'Authorization': f'Bearer {bearer_token}',
                })
        except ExtractorError as e:
            if isinstance(e.cause, HTTPError) and e.cause.status == 401:
                self._set_access_token(None)
                self._refresh_token = None
                self._cache_tokens()
                raise ExtractorError('Your tokens have been invalidated', expected=True)
            raise

        self._set_access_token(response['access_token'])
        if refresh_token := traverse_obj(response, ('refresh_token', {str})):
            self.write_debug('New refresh token granted')
            self._refresh_token = refresh_token
        self._cache_tokens()