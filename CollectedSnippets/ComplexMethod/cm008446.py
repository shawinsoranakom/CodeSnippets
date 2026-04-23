def _real_extract(self, url):
        video_id = self._match_id(url)
        geo_country = self._search_regex(
            r'https?://[^/]+\.([a-z]{2})', url,
            'geo country', default=None)
        if geo_country:
            self._initialize_geo_bypass({'countries': [geo_country.upper()]})
        video = self._download_json(
            f'http://playapi.mtgx.tv/v3/videos/{video_id}', video_id, 'Downloading video JSON')

        title = video['title']

        try:
            streams = self._download_json(
                f'http://playapi.mtgx.tv/v3/videos/stream/{video_id}',
                video_id, 'Downloading streams JSON')
        except ExtractorError as e:
            if isinstance(e.cause, HTTPError) and e.cause.status == 403:
                msg = self._parse_json(e.cause.response.read().decode('utf-8'), video_id)
                raise ExtractorError(msg['msg'], expected=True)
            raise

        quality = qualities(['hls', 'medium', 'high'])
        formats = []
        for format_id, video_url in streams.get('streams', {}).items():
            video_url = url_or_none(video_url)
            if not video_url:
                continue
            ext = determine_ext(video_url)
            if ext == 'f4m':
                formats.extend(self._extract_f4m_formats(
                    update_url_query(video_url, {
                        'hdcore': '3.5.0',
                        'plugin': 'aasp-3.5.0.151.81',
                    }), video_id, f4m_id='hds', fatal=False))
            elif ext == 'm3u8':
                formats.extend(self._extract_m3u8_formats(
                    video_url, video_id, 'mp4', 'm3u8_native',
                    m3u8_id='hls', fatal=False))
            else:
                fmt = {
                    'format_id': format_id,
                    'quality': quality(format_id),
                    'ext': ext,
                }
                if video_url.startswith('rtmp'):
                    m = re.search(
                        r'^(?P<url>rtmp://[^/]+/(?P<app>[^/]+))/(?P<playpath>.+)$', video_url)
                    if not m:
                        continue
                    fmt.update({
                        'ext': 'flv',
                        'url': m.group('url'),
                        'app': m.group('app'),
                        'play_path': m.group('playpath'),
                        'preference': -1,
                    })
                else:
                    fmt.update({
                        'url': video_url,
                    })
                formats.append(fmt)

        if not formats and video.get('is_geo_blocked'):
            self.raise_geo_restricted(
                'This content might not be available in your country due to copyright reasons',
                metadata_available=True)

        # TODO: webvtt in m3u8
        subtitles = {}
        sami_path = video.get('sami_path')
        if sami_path:
            lang = self._search_regex(
                r'_([a-z]{2})\.xml', sami_path, 'lang',
                default=urllib.parse.urlparse(url).netloc.rsplit('.', 1)[-1])
            subtitles[lang] = [{
                'url': sami_path,
            }]

        series = video.get('format_title')
        episode_number = int_or_none(video.get('format_position', {}).get('episode'))
        season = video.get('_embedded', {}).get('season', {}).get('title')
        season_number = int_or_none(video.get('format_position', {}).get('season'))

        return {
            'id': video_id,
            'title': title,
            'description': video.get('description'),
            'series': series,
            'episode_number': episode_number,
            'season': season,
            'season_number': season_number,
            'duration': int_or_none(video.get('duration')),
            'timestamp': parse_iso8601(video.get('created_at')),
            'view_count': try_get(video, lambda x: x['views']['total'], int),
            'age_limit': int_or_none(video.get('age_limit', 0)),
            'formats': formats,
            'subtitles': subtitles,
        }