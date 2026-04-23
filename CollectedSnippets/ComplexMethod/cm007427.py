def _real_initialize(self):
        username, password = self._get_login_info()
        if not username:
            return
        try:
            url = self._API_BASE_URL + 'authentication/login'
            access_token = (self._download_json(
                url, None, 'Logging in', self._LOGIN_ERR_MESSAGE, fatal=False,
                data=urlencode_postdata({
                    'password': password,
                    'rememberMe': False,
                    'source': 'Web',
                    'username': username,
                })) or {}).get('accessToken')
            if access_token:
                self._HEADERS = {'authorization': 'Bearer ' + access_token}
        except ExtractorError as e:
            message = None
            if isinstance(e.cause, compat_HTTPError) and e.cause.code == 401:
                resp = self._parse_json(
                    self._webpage_read_content(e.cause, url, username),
                    username, fatal=False) or {}
                message = resp.get('message') or resp.get('code')
            self.report_warning(message or self._LOGIN_ERR_MESSAGE)