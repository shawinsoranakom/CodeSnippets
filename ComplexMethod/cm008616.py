def _real_extract(self, url):
        display_id = self._match_id(url)

        try:
            data = self._download_json(
                update_url(url, query=None), display_id,
                query={'json': 'true'})
        except ExtractorError as e:
            if isinstance(e.cause, HTTPError) and e.cause.status == 404 and not self.suitable(e.cause.response.url):
                self.raise_geo_restricted(countries=self._GEO_COUNTRIES)
            raise

        flex_wrapper = traverse_obj(data, (
            'children', lambda _, v: v['type'] == 'MainContainer',
            (None, ('children', lambda _, v: v['type'] == 'AviaWrapper')),
            'children', lambda _, v: v['type'] == 'FlexWrapper', {dict}, any))
        video_detail = traverse_obj(flex_wrapper, (
            (None, ('children', lambda _, v: v['type'] == 'AuthSuiteWrapper')),
            'children', lambda _, v: v['type'] == 'Player',
            'props', 'videoDetail', {dict}, any))
        if not video_detail:
            video_detail = traverse_obj(data, (
                'children', ..., ('handleTVEAuthRedirection', None),
                'videoDetail', {dict}, any, {require('video detail')}))

        mgid = video_detail['mgid']
        video_id = mgid.rpartition(':')[2]
        service_url = traverse_obj(video_detail, ('videoServiceUrl', {url_or_none}, {update_url(query=None)}))
        if not service_url:
            raise ExtractorError('This content is no longer available', expected=True)

        headers = {}
        if video_detail.get('authRequired'):
            # The vast majority of provider-locked content has been moved to Paramount+
            # BetIE is the only extractor that is currently known to reach this code path
            video_config = traverse_obj(flex_wrapper, (
                'children', lambda _, v: v['type'] == 'AuthSuiteWrapper',
                'props', 'videoConfig', {dict}, any, {require('video config')}))
            config = traverse_obj(data, (
                'props', 'authSuiteConfig', {dict}, {require('auth suite config')}))
            headers['X-VIA-TVE-MEDIATOKEN'] = self._get_media_token(video_config, config, display_id)

        stream_info = self._download_json(
            service_url, video_id, 'Downloading API JSON', 'Unable to download API JSON',
            query={'clientPlatform': 'desktop'}, headers=headers)['stitchedstream']

        manifest_type = stream_info['manifesttype']
        if manifest_type == 'hls':
            formats, subtitles = self._extract_m3u8_formats_and_subtitles(
                stream_info['source'], video_id, 'mp4', m3u8_id=manifest_type)
        elif manifest_type == 'dash':
            formats, subtitles = self._extract_mpd_formats_and_subtitles(
                stream_info['source'], video_id, mpd_id=manifest_type)
        else:
            self.raise_no_formats(f'Unsupported manifest type "{manifest_type}"')
            formats, subtitles = [], {}

        return {
            **traverse_obj(video_detail, {
                'title': ('title', {str}),
                'channel': ('channel', 'name', {str}),
                'thumbnails': ('images', ..., {'url': ('url', {url_or_none})}),
                'description': (('fullDescription', 'description'), {str}, any),
                'series': ('parentEntity', 'title', {str}),
                'season_number': ('seasonNumber', {int_or_none}),
                'episode_number': ('episodeAiringOrder', {int_or_none}),
                'duration': ('duration', 'milliseconds', {float_or_none(scale=1000)}),
                'timestamp': ((
                    ('originalPublishDate', {parse_iso8601}),
                    ('publishDate', 'timestamp', {int_or_none})), any),
                'release_timestamp': ((
                    ('originalAirDate', {parse_iso8601}),
                    ('airDate', 'timestamp', {int_or_none})), any),
            }),
            'id': video_id,
            'display_id': display_id,
            'formats': formats,
            'subtitles': subtitles,
        }