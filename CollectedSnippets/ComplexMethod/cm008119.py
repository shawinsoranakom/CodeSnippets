def _call_api(self, ep, video_id, **kwargs):
        for first_attempt in True, False:
            if 'authorization' not in self._API_HEADERS:
                self._fetch_oauth_token(video_id)
            try:
                headers = dict(self._API_HEADERS)
                headers['x-customheader'] = f'https://www.redgifs.com/watch/{video_id}'
                data = self._download_json(
                    f'https://api.redgifs.com/v2/{ep}', video_id, headers=headers, **kwargs)
                break
            except ExtractorError as e:
                if first_attempt and isinstance(e.cause, HTTPError) and e.cause.status == 401:
                    del self._API_HEADERS['authorization']  # refresh the token
                    continue
                raise

        if 'error' in data:
            raise ExtractorError(f'RedGifs said: {data["error"]}', expected=True, video_id=video_id)
        return data