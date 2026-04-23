def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)
        app_state = self._parse_json(self._search_regex(
            r'<script>window\.APP_STATE\s*=\s*({.+?})</script>',
            webpage, 'app state'), video_id)
        video_data = {}
        getters = list(
            lambda x, k=k: x['initialState']['content%s' % k]['content']
            for k in ('Data', 'Detail')
        )
        for v in app_state.values():
            content = try_get(v, getters, dict)
            if content and content.get('contentId') == video_id:
                video_data = content
                break

        title = video_data['title']

        if video_data.get('drmProtected'):
            raise ExtractorError('This video is DRM protected.', expected=True)

        headers = {'Referer': url}
        formats = []
        geo_restricted = False

        if not self._USER_TOKEN:
            self._DEVICE_ID = compat_str(uuid.uuid4())
            self._USER_TOKEN = self._call_api_v2('um/v3/users', video_id, {
                'X-HS-Platform': 'PCTV',
                'Content-Type': 'application/json',
            }, data=json.dumps({
                'device_ids': [{
                    'id': self._DEVICE_ID,
                    'type': 'device_id',
                }],
            }).encode())['user_identity']

        playback_sets = self._call_api_v2(
            'play/v2/playback/content/' + video_id, video_id, {
                'X-HS-Platform': 'web',
                'X-HS-AppVersion': '6.99.1',
                'X-HS-UserToken': self._USER_TOKEN,
            }, query={
                'device-id': self._DEVICE_ID,
                'desired-config': 'encryption:plain',
                'os-name': 'Windows',
                'os-version': '10',
            })['data']['playBackSets']
        for playback_set in playback_sets:
            if not isinstance(playback_set, dict):
                continue
            format_url = url_or_none(playback_set.get('playbackUrl'))
            if not format_url:
                continue
            format_url = re.sub(
                r'(?<=//staragvod)(\d)', r'web\1', format_url)
            tags = str_or_none(playback_set.get('tagsCombination')) or ''
            if tags and 'encryption:plain' not in tags:
                continue
            ext = determine_ext(format_url)
            try:
                if 'package:hls' in tags or ext == 'm3u8':
                    formats.extend(self._extract_m3u8_formats(
                        format_url, video_id, 'mp4',
                        entry_protocol='m3u8_native',
                        m3u8_id='hls', headers=headers))
                elif 'package:dash' in tags or ext == 'mpd':
                    formats.extend(self._extract_mpd_formats(
                        format_url, video_id, mpd_id='dash', headers=headers))
                elif ext == 'f4m':
                    # produce broken files
                    pass
                else:
                    formats.append({
                        'url': format_url,
                        'width': int_or_none(playback_set.get('width')),
                        'height': int_or_none(playback_set.get('height')),
                    })
            except ExtractorError as e:
                if isinstance(e.cause, compat_HTTPError) and e.cause.code == 403:
                    geo_restricted = True
                continue
        if not formats and geo_restricted:
            self.raise_geo_restricted(countries=['IN'])
        self._sort_formats(formats)

        for f in formats:
            f.setdefault('http_headers', {}).update(headers)

        image = try_get(video_data, lambda x: x['image']['h'], compat_str)

        return {
            'id': video_id,
            'title': title,
            'thumbnail': 'https://img1.hotstarext.com/image/upload/' + image if image else None,
            'description': video_data.get('description'),
            'duration': int_or_none(video_data.get('duration')),
            'timestamp': int_or_none(video_data.get('broadcastDate') or video_data.get('startDate')),
            'formats': formats,
            'channel': video_data.get('channelName'),
            'channel_id': str_or_none(video_data.get('channelId')),
            'series': video_data.get('showName'),
            'season': video_data.get('seasonName'),
            'season_number': int_or_none(video_data.get('seasonNo')),
            'season_id': str_or_none(video_data.get('seasonId')),
            'episode': title,
            'episode_number': int_or_none(video_data.get('episodeNo')),
        }