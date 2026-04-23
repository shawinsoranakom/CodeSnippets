def _real_extract(self, url):
        display_id = self._match_id(url)
        webpage = self._download_webpage(url, display_id)

        def _search_kane(name):
            return self._search_regex(
                r"KANE_customdimensions\.%s\s*=\s*'([^']+)';" % name,
                webpage, name, default=None)

        title_data = self._parse_json(self._search_regex(
            r'TITLE_DATA\s*=\s*({[^}]+})',
            webpage, 'title data', default=''),
            display_id, js_to_json, fatal=False) or {}

        video_id = title_data.get('id') or self._search_regex([
            r"KANE_customdimensions.videoID\s*=\s*'(\d+)';",
            r'<iframe[^>]+src="/player/(\d+)',
        ], webpage, 'video_id', default=None)
        if not video_id:
            player_url = self._html_search_meta([
                'al:web:url',
                'og:video:url',
                'og:video:secure_url',
            ], webpage, fatal=True)
            video_id = self._search_regex(r'/player/(\d+)', player_url, 'video id')

        title = episode = title_data.get('title') or _search_kane('videoTitle') or self._og_search_title(webpage)
        series = _search_kane('showName')
        if series:
            title = '%s - %s' % (series, title)
        description = self._html_search_meta(['description', 'og:description'], webpage, fatal=True)

        try:
            headers = {}
            if self._TOKEN:
                headers['Authorization'] = 'Token %s' % self._TOKEN
            sources = self._download_json(
                'https://www.funimation.com/api/showexperience/%s/' % video_id,
                video_id, headers=headers, query={
                    'pinst_id': ''.join([random.choice(string.digits + string.ascii_letters) for _ in range(8)]),
                })['items']
        except ExtractorError as e:
            if isinstance(e.cause, compat_HTTPError) and e.cause.code == 403:
                error = self._parse_json(e.cause.read(), video_id)['errors'][0]
                raise ExtractorError('%s said: %s' % (
                    self.IE_NAME, error.get('detail') or error.get('title')), expected=True)
            raise

        formats = []
        for source in sources:
            source_url = source.get('src')
            if not source_url:
                continue
            source_type = source.get('videoType') or determine_ext(source_url)
            if source_type == 'm3u8':
                formats.extend(self._extract_m3u8_formats(
                    source_url, video_id, 'mp4',
                    m3u8_id='hls', fatal=False))
            else:
                formats.append({
                    'format_id': source_type,
                    'url': source_url,
                })
        self._sort_formats(formats)

        return {
            'id': video_id,
            'display_id': display_id,
            'title': title,
            'description': description,
            'thumbnail': self._og_search_thumbnail(webpage),
            'series': series,
            'season_number': int_or_none(title_data.get('seasonNum') or _search_kane('season')),
            'episode_number': int_or_none(title_data.get('episodeNum')),
            'episode': episode,
            'season_id': title_data.get('seriesId'),
            'formats': formats,
        }