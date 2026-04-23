def _real_extract(self, url):
        display_id = self._match_id(url)
        access_token, video_token = self._fetch_tokens()

        metadata = self._download_json(
            f'https://www.vrt.be/vrtnu-api/graphql{"" if access_token else "/public"}/v1',
            display_id, 'Downloading asset JSON', 'Unable to download asset JSON',
            data=json.dumps({
                'operationName': 'VideoPage',
                'query': self._VIDEO_PAGE_QUERY,
                'variables': {'pageId': urllib.parse.urlparse(url).path},
            }).encode(),
            headers=filter_dict({
                'Authorization': f'Bearer {access_token}' if access_token else None,
                'Content-Type': 'application/json',
                'x-vrt-client-name': 'WEB',
                'x-vrt-client-version': '1.5.9',
                'x-vrt-zone': 'default',
            }))['data']['page']

        video_id = metadata['player']['modes'][0]['streamId']

        try:
            streaming_info = self._call_api(video_id, 'vrtnu-web@PROD', id_token=video_token)
        except ExtractorError as e:
            if not video_token and isinstance(e.cause, HTTPError) and e.cause.status == 404:
                self.raise_login_required()
            raise

        formats, subtitles = self._extract_formats_and_subtitles(streaming_info, video_id)

        code = traverse_obj(streaming_info, ('code', {str}))
        if not formats and code:
            if code in ('CONTENT_AVAILABLE_ONLY_FOR_BE_RESIDENTS', 'CONTENT_AVAILABLE_ONLY_IN_BE', 'CONTENT_UNAVAILABLE_VIA_PROXY'):
                self.raise_geo_restricted(countries=['BE'])
            elif code in ('CONTENT_AVAILABLE_ONLY_FOR_BE_RESIDENTS_AND_EXPATS', 'CONTENT_IS_AGE_RESTRICTED', 'CONTENT_REQUIRES_AUTHENTICATION'):
                self.raise_login_required()
            else:
                self.raise_no_formats(f'Unable to extract formats: {code}')

        return {
            'duration': float_or_none(streaming_info.get('duration'), 1000),
            'thumbnail': url_or_none(streaming_info.get('posterImageUrl')),
            **self._json_ld(traverse_obj(metadata, ('ldjson', ..., {json.loads})), video_id, fatal=False),
            **traverse_obj(metadata, ('episode', {
                'title': ('title', {str}),
                'description': ('description', {str}),
                'timestamp': ('onTimeRaw', {parse_iso8601}),
                'series': ('program', 'title', {str}),
                'season': ('season', 'titleRaw', {str}),
                'season_number': ('season', 'titleRaw', {int_or_none}),
                'season_id': ('id', {str_or_none}),
                'episode': ('title', {str}),
                'episode_number': ('episodeNumberRaw', {int_or_none}),
                'episode_id': ('id', {str_or_none}),
                'age_limit': ('ageRaw', {parse_age_limit}),
                'channel': ('brand', {str}),
                'duration': ('durationRaw', {parse_duration}),
            })),
            'id': video_id,
            'display_id': display_id,
            'formats': formats,
            'subtitles': subtitles,
            '_old_archive_ids': [make_archive_id('Canvas', video_id),
                                 make_archive_id('Ketnet', video_id)],
        }