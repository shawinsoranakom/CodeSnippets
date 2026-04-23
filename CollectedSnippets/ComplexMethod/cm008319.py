def _real_extract(self, url):
        video_id = self._match_id(url)

        path = 'v3' if self.is_logged_in else 'v3_guest'
        api_resp = self._download_json(
            f'{self._BASE_URL}/api/watch/{path}/{video_id}', video_id,
            'Downloading API JSON', 'Unable to fetch data', headers={
                **self._HEADERS,
                **self.geo_verification_headers(),
            }, query={
                'actionTrackId': f'AAAAAAAAAA_{round(time_seconds() * 1000)}',
            }, expected_status=[400, 404])

        api_data = api_resp['data']
        scheduled_time = traverse_obj(api_data, ('publishScheduledAt', {str}))
        status = traverse_obj(api_resp, ('meta', 'status', {int}))

        if status != 200:
            err_code = traverse_obj(api_resp, ('meta', 'errorCode', {str.upper}))
            reason_code = traverse_obj(api_data, ('reasonCode', {str_or_none}))
            err_msg = traverse_obj(self._ERROR_MAP, (err_code, (reason_code, 'DEFAULT'), {str}, any))

            if reason_code in ('DOMESTIC_VIDEO', 'HIGH_RISK_COUNTRY_VIDEO'):
                self.raise_geo_restricted(countries=self._GEO_COUNTRIES)
            elif reason_code == 'HARMFUL_VIDEO' and traverse_obj(api_data, (
                'viewer', 'allowSensitiveContents', {bool},
            )) is False:
                err_msg = 'Sensitive content, adjust display settings to watch'
            elif reason_code == 'HIDDEN_VIDEO' and scheduled_time:
                err_msg = f'This content is scheduled to be released at {scheduled_time}'
            elif reason_code in ('CHANNEL_MEMBER_ONLY', 'HARMFUL_VIDEO', 'HIDDEN_VIDEO', 'PPV_VIDEO', 'PREMIUM_ONLY'):
                self.raise_login_required(err_msg)

            if err_msg:
                raise ExtractorError(err_msg, expected=True)
            if status and status >= 500:
                raise ExtractorError('Service temporarily unavailable', expected=True)
            raise ExtractorError(f'API returned error status {status}')

        availability = self._availability(**traverse_obj(api_data, ('payment', 'video', {
            'needs_auth': (('isContinuationBenefit', 'isPpv'), {bool}, any),
            'needs_subscription': ('isAdmission', {bool}),
            'needs_premium': ('isPremium', {bool}),
        }))) or 'public'

        formats = self._extract_formats(api_data, video_id)
        err_msg = self._STATUS_MAP.get(availability)
        if not formats and err_msg:
            self.raise_login_required(err_msg, metadata_available=True)

        thumb_prefs = qualities(['url', 'middleUrl', 'largeUrl', 'player', 'ogp'])

        return {
            'availability': availability,
            'display_id': video_id,
            'formats': formats,
            'genres': traverse_obj(api_data, ('genre', 'label', {str}, filter, all, filter)),
            'release_timestamp': parse_iso8601(scheduled_time),
            'subtitles': self.extract_subtitles(video_id, api_data),
            'tags': traverse_obj(api_data, ('tag', 'items', ..., 'name', {str}, filter, all, filter)),
            'thumbnails': [{
                'ext': 'jpg',
                'id': key,
                'preference': thumb_prefs(key),
                'url': url,
                **parse_resolution(url, lenient=True),
            } for key, url in traverse_obj(api_data, (
                'video', 'thumbnail', {dict}), default={}).items()],
            **traverse_obj(api_data, (('channel', 'owner'), any, {
                'channel': (('name', 'nickname'), {str}, any),
                'channel_id': ('id', {str_or_none}),
                'uploader': (('name', 'nickname'), {str}, any),
                'uploader_id': ('id', {str_or_none}),
            })),
            **traverse_obj(api_data, ('video', {
                'id': ('id', {str_or_none}),
                'title': ('title', {str}),
                'description': ('description', {clean_html}, filter),
                'duration': ('duration', {int_or_none}),
                'timestamp': ('registeredAt', {parse_iso8601}),
            })),
            **traverse_obj(api_data, ('video', 'count', {
                'comment_count': ('comment', {int_or_none}),
                'like_count': ('like', {int_or_none}),
                'view_count': ('view', {int_or_none}),
            })),
        }