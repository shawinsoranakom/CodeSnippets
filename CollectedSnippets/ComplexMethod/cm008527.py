def _TOKEN(self):
        if not self._REAL_TOKEN or not self._TOKEN_EXPIRY:
            token = try_call(lambda: self._get_cookies('https://www.wrestle-universe.com/')['token'].value)
            if not token and not self._REFRESH_TOKEN:
                self.raise_login_required()
            self._TOKEN = token

        if not self._REAL_TOKEN or self._TOKEN_EXPIRY <= int(time.time()):
            if not self._REFRESH_TOKEN:
                raise ExtractorError(
                    'Expired token. Refresh your cookies in browser and try again', expected=True)
            self._refresh_token()

        return self._REAL_TOKEN