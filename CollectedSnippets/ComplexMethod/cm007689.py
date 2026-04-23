def _extract_video(self, params):
        video_id = params['videoId']

        video_info = None

        # New API path
        query = params.copy()
        query['embedType'] = 'inline'
        info_page = self._download_json(
            'http://player.cnevids.com/embed-api.json', video_id,
            'Downloading embed info', fatal=False, query=query)

        # Old fallbacks
        if not info_page:
            if params.get('playerId'):
                info_page = self._download_json(
                    'http://player.cnevids.com/player/video.js', video_id,
                    'Downloading video info', fatal=False, query=params)
        if info_page:
            video_info = info_page.get('video')
        if not video_info:
            info_page = self._download_webpage(
                'http://player.cnevids.com/player/loader.js',
                video_id, 'Downloading loader info', query=params)
        if not video_info:
            info_page = self._download_webpage(
                'https://player.cnevids.com/inline/video/%s.js' % video_id,
                video_id, 'Downloading inline info', query={
                    'target': params.get('target', 'embedplayer')
                })

        if not video_info:
            video_info = self._parse_json(
                self._search_regex(
                    r'(?s)var\s+config\s*=\s*({.+?});', info_page, 'config'),
                video_id, transform_source=js_to_json)['video']

        title = video_info['title']

        formats = []
        for fdata in video_info['sources']:
            src = fdata.get('src')
            if not src:
                continue
            ext = mimetype2ext(fdata.get('type')) or determine_ext(src)
            if ext == 'm3u8':
                formats.extend(self._extract_m3u8_formats(
                    src, video_id, 'mp4', entry_protocol='m3u8_native',
                    m3u8_id='hls', fatal=False))
                continue
            quality = fdata.get('quality')
            formats.append({
                'format_id': ext + ('-%s' % quality if quality else ''),
                'url': src,
                'ext': ext,
                'quality': 1 if quality == 'high' else 0,
            })
        self._sort_formats(formats)

        subtitles = {}
        for t, caption in video_info.get('captions', {}).items():
            caption_url = caption.get('src')
            if not (t in ('vtt', 'srt', 'tml') and caption_url):
                continue
            subtitles.setdefault('en', []).append({'url': caption_url})

        return {
            'id': video_id,
            'formats': formats,
            'title': title,
            'thumbnail': video_info.get('poster_frame'),
            'uploader': video_info.get('brand'),
            'duration': int_or_none(video_info.get('duration')),
            'tags': video_info.get('tags'),
            'series': video_info.get('series_title'),
            'season': video_info.get('season_title'),
            'timestamp': parse_iso8601(video_info.get('premiere_date')),
            'categories': video_info.get('categories'),
            'subtitles': subtitles,
        }