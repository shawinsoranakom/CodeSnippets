def _call_playback_api(self, content_id):
        if self._access_token and self._is_jwt_expired(self._access_token):
            self._refresh_access_token()
        for is_retry in (False, True):
            try:
                return self._download_json_handle(
                    f'https://10.com.au/api/v1/videos/playback/{content_id}/', content_id,
                    note='Downloading video JSON', query={'platform': 'samsung'},
                    headers=filter_dict({
                        'TP-AcceptFeature': 'v1/fw;v1/drm',
                        'Authorization': f'Bearer {self._access_token}' if self._access_token else None,
                    }))
            except ExtractorError as e:
                if not is_retry and isinstance(e.cause, HTTPError) and e.cause.status == 403:
                    if self._access_token:
                        self.to_screen('Access token has expired; refreshing')
                        self._refresh_access_token()
                        continue
                    elif not self._get_login_info()[0]:
                        self.raise_login_required('Login required to access this video', method='password')
                raise