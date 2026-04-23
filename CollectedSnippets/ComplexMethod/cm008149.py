def _call_api(self, ep, video_id, data=None, note='Downloading API JSON'):
        # Ref: https://ssl.pstatic.net/static/wevweb/2_3_2_11101725/public/static/js/2488.a09b41ff.chunk.js
        # From https://ssl.pstatic.net/static/wevweb/2_3_2_11101725/public/static/js/main.e206f7c1.js:
        api_path = update_url_query(ep, {
            # 'gcc': 'US',
            'appId': 'be4d79eb8fc7bd008ee82c8ec4ff6fd4',
            'language': 'en',
            'os': self._CLIENT_PLATFORM,
            'platform': self._CLIENT_PLATFORM,
            'wpf': 'pc',
        })
        for is_retry in (False, True):
            wmsgpad = int(time.time() * 1000)
            wmd = base64.b64encode(hmac.HMAC(
                self._SIGNING_KEY, f'{api_path[:255]}{wmsgpad}'.encode(),
                digestmod=hashlib.sha1).digest()).decode()

            try:
                return self._download_json(
                    f'https://global.apis.naver.com/weverse/wevweb{api_path}', video_id, note=note,
                    data=data, headers={
                        **self._API_HEADERS,
                        **self._get_authorization_header(),
                        **({'Content-Type': 'application/json'} if data else {}),
                        'WEV-device-Id': self._device_id,
                    }, query={
                        'wmsgpad': wmsgpad,
                        'wmd': wmd,
                    })
            except ExtractorError as e:
                if is_retry or not isinstance(e.cause, HTTPError):
                    raise
                elif self._is_logged_in and e.cause.status == 401:
                    self._refresh_access_token()
                    continue
                elif e.cause.status == 403:
                    if self._is_logged_in:
                        raise ExtractorError(
                            'Your account does not have access to this content', expected=True)
                    self._report_login_error('login_required')
                raise