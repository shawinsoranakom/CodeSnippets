def _call_api(self, path, video_id):
        url = path if path.startswith('http') else self._API_BASE_URL + path
        for _ in range(2):
            try:
                result = self._download_xml(url, video_id, headers={
                    'X-Clearleap-DeviceId': self._device_id,
                    'X-Clearleap-DeviceToken': self._device_token,
                })
            except ExtractorError as e:
                if isinstance(e.cause, compat_HTTPError) and e.cause.code == 401:
                    # Device token has expired, re-acquiring device token
                    self._register_device()
                    continue
                raise
        error_message = xpath_text(result, 'userMessage') or xpath_text(result, 'systemMessage')
        if error_message:
            raise ExtractorError('%s said: %s' % (self.IE_NAME, error_message))
        return result