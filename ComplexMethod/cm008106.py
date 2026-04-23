def _real_extract(self, url):
        mobj = self._match_valid_url(url)

        track_id = mobj.group('track_id')

        query = {}
        if track_id:
            info_json_url = self._API_V2_BASE + 'tracks/' + track_id
            full_title = track_id
            token = mobj.group('secret_token')
            if token:
                query['secret_token'] = token
        else:
            full_title = resolve_title = '{}/{}'.format(*mobj.group('uploader', 'title'))
            token = mobj.group('token')
            if token:
                resolve_title += f'/{token}'
            info_json_url = self._resolv_url(self._BASE_URL + resolve_title)

        info = self._call_api(
            info_json_url, full_title, 'Downloading info JSON', query=query, headers=self._HEADERS)

        for retry in self.RetryManager():
            try:
                return self._extract_info_dict(info, full_title, token)
            except ExtractorError as e:
                if not isinstance(e.cause, HTTPError) or e.cause.status != 429:
                    raise
                self.report_warning(
                    'You have reached the API rate limit, which is ~600 requests per '
                    '10 minutes. Use the --extractor-retries and --retry-sleep options '
                    'to configure an appropriate retry count and wait time', only_once=True)
                retry.error = e.cause