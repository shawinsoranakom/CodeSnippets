def _real_extract(self, url):
        video_id = self._match_id(url)

        self._access_token = self._call_api(
            f'previewpassmvpd?device_id={self._device_id}&mvpd_id=TempPass_fbcfox_60min',
            video_id)['accessToken']

        video = self._call_api('watch', video_id, data=json.dumps({
            'capabilities': ['drm/widevine', 'fsdk/yo'],
            'deviceWidth': 1280,
            'deviceHeight': 720,
            'maxRes': '720p',
            'os': 'macos',
            'osv': '',
            'provider': {
                'freewheel': {'did': self._device_id},
                'vdms': {'rays': ''},
                'dmp': {'kuid': '', 'seg': ''},
            },
            'playlist': '',
            'privacy': {'us': '1---'},
            'siteSection': '',
            'streamType': 'vod',
            'streamId': video_id}).encode())

        title = video['name']
        release_url = video['url']

        try:
            m3u8_url = self._download_json(release_url, video_id)['playURL']
        except ExtractorError as e:
            if isinstance(e.cause, HTTPError) and e.cause.status == 403:
                error = self._parse_json(e.cause.response.read().decode(), video_id)
                if error.get('exception') == 'GeoLocationBlocked':
                    self.raise_geo_restricted(countries=['US'])
                raise ExtractorError(error['description'], expected=True)
            raise
        formats = self._extract_m3u8_formats(
            m3u8_url, video_id, 'mp4',
            entry_protocol='m3u8_native', m3u8_id='hls')

        data = try_get(
            video, lambda x: x['trackingData']['properties'], dict) or {}

        duration = int_or_none(video.get('durationInSeconds')) or int_or_none(
            video.get('duration')) or parse_duration(video.get('duration'))
        timestamp = unified_timestamp(video.get('datePublished'))
        creator = data.get('brand') or data.get('network') or video.get('network')
        series = video.get('seriesName') or data.get(
            'seriesName') or data.get('show')

        subtitles = {}
        for doc_rel in video.get('documentReleases', []):
            rel_url = doc_rel.get('url')
            if not url or doc_rel.get('format') != 'SCC':
                continue
            subtitles['en'] = [{
                'url': rel_url,
                'ext': 'scc',
            }]
            break

        return {
            'id': video_id,
            'title': title,
            'formats': formats,
            'description': video.get('description'),
            'duration': duration,
            'timestamp': timestamp,
            'age_limit': parse_age_limit(video.get('contentRating')),
            'creator': creator,
            'series': series,
            'season_number': int_or_none(video.get('seasonNumber')),
            'episode': video.get('name'),
            'episode_number': int_or_none(video.get('episodeNumber')),
            'thumbnail': traverse_obj(video, ('images', 'still', 'raw'), expected_type=url_or_none),
            'release_year': int_or_none(video.get('releaseYear')),
            'subtitles': subtitles,
        }