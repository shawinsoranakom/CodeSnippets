def _fetch_tokens(self):
        has_credentials = self._get_login_info()[0]
        access_token = self._get_vrt_cookie(self._ACCESS_TOKEN_COOKIE_NAME)
        video_token = self._get_vrt_cookie(self._VIDEO_TOKEN_COOKIE_NAME)

        if (access_token and not self._is_jwt_token_expired(access_token)
                and video_token and not self._is_jwt_token_expired(video_token)):
            return access_token, video_token

        if has_credentials:
            access_token, video_token = self.cache.load(self._NETRC_MACHINE, 'token_data', default=(None, None))

            if (access_token and not self._is_jwt_token_expired(access_token)
                    and video_token and not self._is_jwt_token_expired(video_token)):
                self.write_debug('Restored tokens from cache')
                self._set_cookie(self._TOKEN_COOKIE_DOMAIN, self._ACCESS_TOKEN_COOKIE_NAME, access_token)
                self._set_cookie(self._TOKEN_COOKIE_DOMAIN, self._VIDEO_TOKEN_COOKIE_NAME, video_token)
                return access_token, video_token

        if not self._get_vrt_cookie(self._REFRESH_TOKEN_COOKIE_NAME):
            return None, None

        self._request_webpage(
            'https://www.vrt.be/vrtmax/sso/refresh', None,
            note='Refreshing tokens', errnote='Failed to refresh tokens', fatal=False)

        access_token = self._get_vrt_cookie(self._ACCESS_TOKEN_COOKIE_NAME)
        video_token = self._get_vrt_cookie(self._VIDEO_TOKEN_COOKIE_NAME)

        if not access_token or not video_token:
            self.cache.store(self._NETRC_MACHINE, 'refresh_token', None)
            self.cookiejar.clear(self._TOKEN_COOKIE_DOMAIN, '/vrtmax/sso', self._REFRESH_TOKEN_COOKIE_NAME)
            msg = 'Refreshing of tokens failed'
            if not has_credentials:
                self.report_warning(msg)
                return None, None
            self.report_warning(f'{msg}. Re-logging in')
            return self._perform_login(*self._get_login_info())

        if has_credentials:
            self.cache.store(self._NETRC_MACHINE, 'token_data', (access_token, video_token))

        return access_token, video_token